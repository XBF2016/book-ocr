import logging
import textwrap
from pathlib import Path

import cv2

from boocr.ocr import run_ocr

logging.basicConfig(level=logging.INFO)

IMG_PATH = Path("output/ocr_debug/page0_col0.png")

if not IMG_PATH.exists():
    raise FileNotFoundError(f"Image not found: {IMG_PATH}")

img = cv2.imread(str(IMG_PATH))
if img is None:
    raise RuntimeError("Failed to read image with OpenCV")

text = run_ocr(img)
print("OCR Result (preview):")
print(textwrap.shorten(text.replace("\n", " "), width=200, placeholder="..."))
print("\nFull Text:\n", text)
