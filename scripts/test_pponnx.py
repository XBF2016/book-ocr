from pponnxcr import TextSystem
import cv2, textwrap
ocr = TextSystem('zht')
img = cv2.imread('output/ocr_debug/page0_col0.png')
print('predicting...')
text = ocr.ocr_single_line(img)
print(text)
