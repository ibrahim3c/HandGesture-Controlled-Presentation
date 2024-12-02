import time
import cv2 as cv
import os
from cvzone.HandTrackingModule import HandDetector
import numpy as np


# vars
width,height=1280,720
folderPath="images"

# camera
cap = cv.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# get presentation images in list
# i want to sort them by name
ImagesPath=sorted(os.listdir(folderPath),key=lambda x:int(x.split('.')[0]))
print(ImagesPath)

# vars
imgNumber=0
hMyImage,wMyImage=int(120*1),int(213*1)
threshold=400
buttonPressed=False
buttonCounter=0
buttonDelay=30
slideswidth,slidesheight=500,500

# hand detector
detector=HandDetector(detectionCon=0.8,maxHands=1)

while True:
    # get images
    success, img = cap.read()
    # i want to flip the image horizontally => for mirroring affect 
    img=cv.flip(img,1)
    print(ImagesPath[imgNumber])
    FullPathImage=os.path.join(folderPath,ImagesPath[imgNumber])
    slides=cv.imread(FullPathImage)

    # hand detection
    hands, img=detector.findHands(img)

    # draw line for threshold 
    cv.line(img,(0,threshold),(width,threshold),(255,0,0),8)



    if hands and not buttonPressed:
        # cuz we want only one hand
        hand=hands[0]
        fingers=detector.fingersUp(hand)

         # if value above threshold => hand detected
        if hand['center'][1]<threshold:

            # Gesture 1 =>left
            if fingers==[1,0,0,0,0]:
               print("left")
               if imgNumber > 0:
                    imgNumber -= 1
                    buttonPressed=True
            # Gesture 1 =>right
            if fingers==[0,0,0,0,1]:
               if imgNumber < len(ImagesPath) - 1:
                    imgNumber += 1
                    buttonPressed=True

        # gesture 3 => show pointer
        # it is not limited to above threshold
        if fingers==[0,1,1,0,0]:
            indexFinger=hand['lmList'][8]
            xval=int(np.interp(indexFinger[0],(width // 2,w),(0,width)))
            yval=int(np.interp(indexFinger[1],(150,height-150),(0,height)))
            indexFinger=xval,yval
            cv.circle(slides,(indexFinger[0],indexFinger[1]),10,(0,255,0),cv.FILLED)
    
    # button pressed iteration
    if buttonPressed:
        buttonCounter+=1
        # buttonDelay is number of frames to wait after button press
        if buttonCounter>buttonDelay:
            buttonCounter=0     
            buttonPressed=False


    # resize my image and put it in slide 
    myImage=cv.resize(img,(wMyImage,hMyImage))
    h,w,c=slides.shape
    slides[0:hMyImage,w-wMyImage:w]=myImage
    print(hMyImage,wMyImage)

    # display
    # cv.imshow("Image", img)
    cv.imshow("slides", slides)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break