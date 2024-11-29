import cv2 as cv
import os
from cvzone.HandTrackingModule import HandDetector


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
imgNumber=2
hMyImage,wMyImage=int(120*1),int(213*1)

# hand detector
detector=HandDetector(detectionCon=0.8,maxHands=1)

while True:
    # get images
    success, img = cap.read()
    # i want to flip the image horizontally
    img=cv.flip(img,1)
    FullPathImage=os.path.join(folderPath,ImagesPath[imgNumber])
    curImage=cv.imread(FullPathImage)

    # hand detection
    hands, img=detector.findHands(img,flipType=False)

    # resize my image and put it in silde 
    myImage=cv.resize(img,(wMyImage,hMyImage))
    h,w,c=myImage.shape
    curImage[0:hMyImage,w-wMyImage:w]=myImage

    # display
    cv.imshow("myImage", img)
    cv.imshow("slides", curImage)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break