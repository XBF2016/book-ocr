import os, sys, pathlib
# 确保 PaddleOCR 模型下载源走 BOS 镜像，避免 404
os.environ.setdefault('PADDLE_PDX_MODEL_SOURCE', 'BOS')
# 将项目根目录加入 PYTHONPATH，避免 import boocr 失败
root_path = pathlib.Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import cv2, logging
from boocr.ocr import create_ocr_engine
from boocr.dataclasses import ColumnCrop

logging.basicConfig(level=logging.INFO)
img = cv2.imread('output/ocr_debug/page0_col0.png')
if img is None:
    raise RuntimeError('Image load fail')

engine = create_ocr_engine(use_gpu=False, auto_download=False)

h, w = img.shape[:2]
col = ColumnCrop(page_index=0, column_index=0, bbox=(0,0,w,h), image=img)
result = engine.run_ocr(col)
print('Confidence:', result.confidence)
print('Text preview:', result.text[:100])
print('Length:', len(result.text))
