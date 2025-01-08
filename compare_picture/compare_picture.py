import cv2
import numpy as np
import matplotlib.pyplot as plt

image1 = cv2.imread('img1.jpg')
image2 = cv2.imread('img2.jpg')

if image1 is None or image2 is None:
    print ("Error: error loading images.")

gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

difference = cv2.absdiff(gray1, gray2)

_, thresh = cv2.threshold(difference, 30, 255, cv2.THRESH_BINARY)

contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for contour in contours:
    if cv2.contourArea(contour) > 100:
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(image1, (x, y), (x + w, y + h), (0, 255, 0), 2)

plt.figure(figsize=(10,5))
plt.subplot(1, 3, 1)
plt.imshow(cv2.cvtColor(image1, cv2.COLOR_BGR2RGB))
plt.title('Diff marked on Image 1')
plt.axis('off')

plt.subplot(1,3,2)
plt.imshow(thresh, cmap='gray')
plt.title('Difference Image')
plt.axis('off')

plt.subplot(1,3,3)
plt.imshow(cv2.cvtColor(image2, cv2.COLOR_BGR2RGB))
plt.title('Image 2')
plt.axis('off')

plt.show()
