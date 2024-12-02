from cvzone.HandTrackingModule import HandDetector
import cv2 as cv
import os
import numpy as np

# vars
width, height = 1280, 720
threshold = 300
folderPath = "images"

imgList = []
delay = 25
buttonPressed = False
counter = 0
drawMode = False
imgNumber = 0
delayCounter = 0
annotations = [[]]
annotationNumber = -1
annotationStart = False
hs, ws = int(120 * 1), int(213 * 1)  # width and height of small image


# Camera Setup
cap = cv.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Hand Detector
Detector = HandDetector(detectionCon=0.8, maxHands=1)


# Get list of presentation images
pathImages = sorted(os.listdir(folderPath), key=len)
print(pathImages)

while True:
    # Get image frame
    success, img = cap.read()
    img = cv.flip(img, 1)
    pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
    slides = cv.imread(pathFullImage)

    # Find the hand 
    hands, img = Detector.findHands(img) 
    # draw line for threshold 
    cv.line(img, (0, threshold), (width, threshold), (0, 255, 0), 10)

    if hands and not buttonPressed :  # If hand is detected

        hand = hands[0]
        cx, cy = hand["center"]
        fingers = Detector.fingersUp(hand)  # list of fingers up


        if cy <= threshold:  # If hand is at the height of the face
            if fingers == [1, 0, 0, 0, 0]:
                print("Left")
                buttonPressed = True
                if imgNumber > 0:
                    imgNumber -= 1
                    annotations = [[]]
                    annotationNumber = -1
                    annotationStart = False
            if fingers == [0, 0, 0, 0, 1]:
                print("Right")
                buttonPressed = True
                if imgNumber < len(pathImages) - 1:
                    imgNumber += 1
                    annotations = [[]]
                    annotationNumber = -1
                    annotationStart = False

        # Gesture 3 => show pointer
        # it is not limited to above threshold
        if fingers == [0, 1, 1, 0, 0]:
            # Constrain values fordrawing => to make it smooth
            lmList = hand["lmList"]  # List of 21 Landmark points
            xVal = int(np.interp(lmList[8][0], [width // 2, width], [0, width]))
            yVal = int(np.interp(lmList[8][1], [150, height-150], [0, height]))
            indexFinger = xVal, yVal
            cv.circle(slides, indexFinger, 9, (0, 0, 255), cv.FILLED)

        if fingers == [0, 1, 0, 0, 0]:
            if annotationStart is False:
                annotationStart = True
                annotationNumber += 1
                annotations.append([])
            print(annotationNumber)
            annotations[annotationNumber].append(indexFinger)
            cv.circle(slides, indexFinger, 12, (0, 0, 255), cv.FILLED)

        else:
            annotationStart = False

        if fingers == [0, 1, 1, 1, 0]:
            if annotations:
                annotations.pop(-1)
                annotationNumber -= 1
                buttonPressed = True

    else:
        annotationStart = False

    if buttonPressed:
        counter += 1
        if counter > delay:
            counter = 0
            buttonPressed = False

    for i, annotation in enumerate(annotations):
        for j in range(len(annotation)):
            if j != 0:
                cv.line(slides, annotation[j - 1], annotation[j], (0, 0, 200), 12)

    imgSmall = cv.resize(img, (ws, hs))
    h, w, _ = slides.shape
    slides[0:hs, w - ws: w] = imgSmall

    cv.imshow("Image", img)
    cv.imshow("Slides", slides)

    key = cv.waitKey(1)
    if key == ord('q'):
        break