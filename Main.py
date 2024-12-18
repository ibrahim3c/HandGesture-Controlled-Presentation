from cvzone.HandTrackingModule import HandDetector
import cv2 as cv
import os
import numpy as np

# constants
width, height = 1280, 720
wSlide, hSlide = 1200, 650
threshold = 300
folderPath = "presentation"
hs, ws = int(120 * 1), int(213 * 1)  # width and height of small image
delay = 25

imgList = []
buttonPressed = False
counter = 0
imgNumber = 0
delayCounter = 0
annotations = [[]]
annotationNumber = -1
annotationStart = True


# Camera Setup
cap = cv.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Hand Detector
Detector = HandDetector(detectionCon=0.8, maxHands=1)


# Get list of presentation images
pathImages = os.listdir(folderPath)
pathImages.sort(key=lambda x: int(os.path.splitext(x)[0]))
# pathImages = sorted(os.listdir(folderPath), key=len)


# Helper Functions
def reset_annotations():
    """Reset all annotations for the current slide."""
    global annotations, annotation_index, annotation_start
    annotations = [[]]
    annotation_index = -1
    annotation_start = True

def get_index_finger_position(lmList):
    """Get the (x, y) position of the index finger tip."""
    xVal = int(np.interp(lmList[8][0], [width // 2, width], [0, width]))
    yVal = int(np.interp(lmList[8][1], [150, height-150], [0, height]))
    return xVal, yVal

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


while True:
    success, img = cap.read()
    img = cv.flip(img, 1)
    pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
    slides = cv.imread(pathFullImage)

    # Find the hand 
    hands, img = Detector.findHands(img) 
    # draw line for threshold 
    cv.line(img, (0, threshold), (width, threshold), (0, 255, 0), 8)

    if hands and not buttonPressed :  

        hand = hands[0]
        cx, cy = hand["center"]
        fingers = Detector.fingersUp(hand)  # list of fingers up


        if cy <= threshold:  # If hand is at the height of the face
            if fingers==[0, 0, 1, 1, 1]:
                break;
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
                if imgNumber < len(pathImages) - 1:
                    imgNumber += 1
                    annotations = [[]]
                    annotationNumber = -1
                    annotationStart = True

        # Gesture 3 => show pointer
        # it is not limited to above threshold
        # Constrain values fordrawing => to make it smooth
        lmList = hand["lmList"]  # List of 21 Landmark points
        indexFinger=get_index_finger_position(lmList)
        if fingers == [0, 1, 1, 0, 0]:
            # cv.circle(slides, indexFinger, 9, (0, 0, 255), cv.FILLED)
            slides=draw_pointer(slides, indexFinger)
            

        # Gesture 4 => draw
        # it is not limited to above threshold
        if fingers == [0, 1, 0, 0, 0]:
            if  annotationStart :
                annotationStart = False
                annotationNumber += 1
                annotations.append([])
            annotations[annotationNumber].append(indexFinger)
            # cv.circle(slides, indexFinger, 5, (0, 0, 255), cv.FILLED)
            slides=highlight_finger(slides, indexFinger)

        else:
            annotationStart = True

        if fingers == [0, 1, 1, 1, 0]:
            if annotations:
                annotations.pop(-1)
                annotationNumber -= 1
                buttonPressed = True
        if fingers == [0, 1, 1, 1, 1]:
            if annotations:
                  annotations.clear();
                  annotationNumber = -1
                  annotationStart = True
                  buttonPressed = True
    else:
        annotationStart = True

    # delaly
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
    # change size of slides
    slides=cv.resize(slides,(wSlide, hSlide))
    h, w, _ = slides.shape
    slides[0:hs, w - ws: w] = sImage

    cv.imshow("Image", img)
    cv.imshow("Slides", slides)

    key = cv.waitKey(1)
    if key == ord('q'):
        break