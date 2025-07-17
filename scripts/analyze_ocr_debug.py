#!/usr/bin/env python
"""统计 output/ocr_debug 下 PNG 调试图像的像素均值和标准差，辅助排查 OCR 图像质量。"""

from pathlib import Path
import cv2
import numpy as np
import sys

DEBUG_DIR = Path(__file__).parent.parent / 'output' / 'ocr_debug'
if not DEBUG_DIR.exists():
    print('调试目录不存在:', DEBUG_DIR, file=sys.stderr)
    sys.exit(1)

files = sorted(DEBUG_DIR.glob('*.png'))
if not files:
    print('调试目录没有 PNG 文件')
    sys.exit(0)

print(f'共发现 {len(files)} 张调试图像')
for f in files:
    img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f'{f.name}: 读取失败')
        continue
    mean = img.mean()
    std = img.std()
    h, w = img.shape
    print(f'{f.name}: {w}x{h}, mean={mean:.1f}, std={std:.1f}')
