import tkinter as tk
from tkinter import filedialog, messagebox
import cv2 as cv
import os
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import fitz  # PyMuPDF library for PDF handling

# Constants
width, height = 1280, 720
wSlide, hSlide = 1200, 650
threshold = 300
hs, ws = int(120 * 1), int(213 * 1)  # Width and height of small image
delay = 25

# Globals
folderPath = ""
imgList = []
buttonPressed = False
counter = 0
imgNumber = 0
delayCounter = 0
annotations = [[]]
annotationNumber = -1
annotationStart = True
is_pdf_loaded = False

def load_folder():
    global folderPath, imgList, imgNumber, is_pdf_loaded
    folderPath = filedialog.askdirectory(title="Select Presentation Folder")
    if not folderPath:
        messagebox.showerror("Error", "No folder selected!")
        return
    
    imgList = [os.path.join(folderPath, f) for f in os.listdir(folderPath) 
               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    imgList.sort()
    
    if not imgList:
        messagebox.showerror("Error", "No images found in the selected folder!")
        return
    
    is_pdf_loaded = False
    messagebox.showinfo("Success", f"Loaded {len(imgList)} images from the folder.")
    imgNumber = 0

def load_pdf():
    global folderPath, imgList, imgNumber, is_pdf_loaded
    pdf_path = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF files", "*.pdf")])
    if not pdf_path:
        messagebox.showerror("Error", "No PDF selected!")
        return
    
    # Create a temporary directory to store PDF pages
    temp_dir = os.path.join(os.path.dirname(pdf_path), "temp_pdf_pages")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Open the PDF and convert pages to images
    try:
        doc = fitz.open(pdf_path)
        imgList = []
        for i, page in enumerate(doc):
            # Render page to an image with higher resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_path = os.path.join(temp_dir, f"{i}.png")
            pix.save(img_path)
            imgList.append(img_path)
        
        folderPath = temp_dir
        is_pdf_loaded = True
        imgNumber = 0
        messagebox.showinfo("Success", f"Loaded {len(imgList)} pages from the PDF.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")
        return

def show_camera():
    global buttonPressed, counter, imgNumber, annotations, annotationNumber, annotationStart

    if not folderPath or not imgList:
        messagebox.showerror("Error", "Please load a folder or PDF first!")
        return

    cap = cv.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)
    detector = HandDetector(detectionCon=0.8, maxHands=1)

    while True:
        success, img = cap.read()
        if not success:
            messagebox.showerror("Error", "Failed to capture camera frame!")
            break

        img = cv.flip(img, 1)
        
        # Read the slide image
        try:
            slides = cv.imread(imgList[imgNumber])
            
            # Ensure slides are loaded correctly
            if slides is None:
                raise ValueError(f"Could not read image: {imgList[imgNumber]}")
            
            # Resize slides to a consistent size
            slides = cv.resize(slides, (wSlide, hSlide), interpolation=cv.INTER_AREA)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load slide: {str(e)}")
            break

        # Find the hand 
        hands, img = detector.findHands(img) 
        # draw line for threshold 
        cv.line(img, (0, threshold), (width, threshold), (0, 255, 0), 8)

        if hands and not buttonPressed:  
            hand = hands[0]
            cx, cy = hand["center"]
            fingers = detector.fingersUp(hand)  # list of fingers up

            if cy <= threshold:  # If hand is at the height of the face
                if fingers == [0, 0, 1, 1, 1]:
                    break
                if fingers == [1, 0, 0, 0, 0]:
                    print("Left")
                    buttonPressed = True
                    if imgNumber > 0:
                        imgNumber -= 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = True

                if fingers == [0, 0, 0, 0, 1]:
                    print("Right")
                    buttonPressed = True
                    if imgNumber < len(imgList) - 1:
                        imgNumber += 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = True

            # Gesture 3 => show pointer
            # it is not limited to above threshold
            # Constrain values for drawing => to make it smooth
            lmList = hand["lmList"]  # List of 21 Landmark points
            indexFinger = get_index_finger_position(lmList)
            
            if fingers == [0, 1, 1, 0, 0]:
                slides = draw_pointer(slides, indexFinger)
                

            # Gesture 4 => draw
            # it is not limited to above threshold
            if fingers == [0, 1, 0, 0, 0]:
                if annotationStart:
                    annotationStart = False
                    annotationNumber += 1
                    annotations.append([])
                annotations[annotationNumber].append(indexFinger)
                slides = highlight_finger(slides, indexFinger)

            else:
                annotationStart = True

            if fingers == [0, 1, 1, 1, 0]:
                if annotations:
                    annotations.pop(-1)
                    annotationNumber -= 1
                    buttonPressed = True
            if fingers == [0, 1, 1, 1, 1]:
                if annotations:
                    annotations.clear()
                    annotationNumber = -1
                    annotationStart = True
                    buttonPressed = True
        else:
            annotationStart = True

        if buttonPressed:
            counter += 1
            if counter > delay:
                counter = 0
                buttonPressed = False

        for i, annotation in enumerate(annotations):
            for j in range(len(annotation)):
                if j != 0:
                    cv.line(slides, annotation[j - 1], annotation[j], (0, 0, 200), 8)
                    

        sImage = cv.resize(img, (ws, hs))
        h, w, _ = slides.shape
        slides[0:hs, w - ws: w] = sImage

        cv.imshow("Image", img)
        cv.imshow("Slides", slides)

        key = cv.waitKey(1)
        if key == ord('q'):
            break

        # Prevent CPU overuse
        cv.waitKey(10)

    cap.release()
    cv.destroyAllWindows()

def get_index_finger_position(lmList):
    """Get the (x, y) position of the index finger tip."""
    # Interpolate finger position to match slide dimensions
    xVal = int(np.interp(lmList[8][0], [width // 2, width], [0, width]))
    yVal = int(np.interp(lmList[8][1], [150, height-150], [0, height]))
    return (xVal, yVal)

def draw_pointer(image, position, pointer_color=(50, 50, 255), shadow_color=(30, 30, 30)):
    """
    Draws a pointer with shadow effects to simulate a 3D appearance with a less opaque shadow.

    :param image: The image on which to draw the pointer.
    :param position: The (x, y) position of the pointer.
    :param pointer_color: The color of the pointer (default is stylized red).
    :param shadow_color: The color of the shadow for the pointer.
    """
    shadow_offset = (8, 8)  
    pointer_radius = 9  # Pointer size
    shadow_radius = pointer_radius + 3  

    shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
    shadow = np.zeros_like(image)  
    cv.circle(shadow, shadow_position, shadow_radius, shadow_color, cv.FILLED)

    image = cv.addWeighted(image, 1, shadow, 0.3, 0)  

    cv.circle(image, position, pointer_radius, pointer_color, cv.FILLED)

    highlight_radius = int(pointer_radius * 0.2)
    highlight_position = (position[0] - pointer_radius // 3, position[1] - pointer_radius // 3)
    cv.circle(image, highlight_position, highlight_radius, (255, 255, 255), cv.FILLED)

    cv.circle(image, position, pointer_radius, (0, 0, 0), 2)

    return image

def highlight_finger(image, finger_position, highlight_radius=30, highlight_color=(0, 0, 255), opacity=0.4):
    """
    Highlights the area around the index finger position with semi-transparency.
    
    :param image: The image on which to highlight the finger.
    :param finger_position: The (x, y) position of the finger to be highlighted.
    :param highlight_radius: The radius of the highlight (default is 30).
    :param highlight_color: The color of the highlight (default is yellow).
    :param opacity: The opacity of the highlight (default is 0.4 for subtle highlighting).
    """
    # Create an overlay image with the same size as the original image
    overlay = image.copy()
    
    # Draw a semi-transparent circle over the finger position
    cv.circle(overlay, finger_position, highlight_radius, highlight_color, -1)

    # Blend the overlay with the original image to create a transparent highlight effect
    cv.addWeighted(overlay, opacity, image, 1 - opacity, 0, image)

    return image

# GUI
root = tk.Tk()
root.title("Hand Gesture Presentation Controller")
root.geometry("400x250")

btn_load_folder = tk.Button(root, text="Load Image Folder", command=load_folder, font=("Arial", 14))
btn_load_folder.pack(pady=10)

btn_load_pdf = tk.Button(root, text="Load PDF", command=load_pdf, font=("Arial", 14))
btn_load_pdf.pack(pady=10)

btn_show_camera = tk.Button(root, text="Show Camera", command=show_camera, font=("Arial", 14))
btn_show_camera.pack(pady=10)

root.mainloop()