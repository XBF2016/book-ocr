#!/usr/bin/env python3
"""Quick utility: run PaddleOCR det+rec on all page_*.png under a P1 directory and save results.

Usage:
    python scripts/quick_auto_det.py [P1_DIR]
If P1_DIR is omitted, the script will try to locate the first output/*/P1 directory.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
from PIL import Image

# Ensure project root on sys.path so that 'boocr' package is discoverable when this script is executed
sys.path.append(str(Path(__file__).resolve().parent.parent))

from boocr.ocr import create_ocr_engine
from boocr.dataclasses import ColumnCrop


def find_default_p1() -> Path:
    """Auto-discover a P1 directory under output/."""
    output_root = Path("output")
    for pdf_dir in output_root.iterdir():
        p1_dir = pdf_dir / "P1"
        if p1_dir.is_dir() and any(p1_dir.glob("page_*.png")):
            return p1_dir
    raise FileNotFoundError("未发现任何 P1 目录，请指定路径参数")


def main():
    # ------------------------------------------------------------------
    # 1. Resolve input P1 directory
    # ------------------------------------------------------------------
    if len(sys.argv) >= 2:
        p1_dir = Path(sys.argv[1])
        if not p1_dir.is_dir():
            print(f"指定的目录不存在: {p1_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        p1_dir = find_default_p1()

    img_paths = sorted(p1_dir.glob("page_*.png"))
    if not img_paths:
        print(f"目录 {p1_dir} 下未找到 page_*.png", file=sys.stderr)
        sys.exit(1)

    print(f"检测到 {len(img_paths)} 页图像, 开始 OCR ...")

    # ------------------------------------------------------------------
    # 2. Initialize OCR engine (det+rec, no rec_only)
    # ------------------------------------------------------------------
    ocr_engine = create_ocr_engine(use_gpu=False, rec_only=False)

    results: List[Dict[str, object]] = []
    for idx, img_path in enumerate(img_paths):
        img = np.array(Image.open(img_path).convert("L"))
        h, w = img.shape[:2]
        crop = ColumnCrop(
            page_index=idx,
            column_index=0,
            bbox=(0, 0, w, h),
            image=img,
        )
        res = ocr_engine.run_ocr(crop)
        preview = res.text.replace("\n", " ")[:120]
        print(f"Page {idx + 1}: conf={res.confidence:.2f} preview='{preview}'")
        results.append({
            "page": idx + 1,
            "confidence": res.confidence,
            "text": res.text,
        })

    # ------------------------------------------------------------------
    # 3. Save JSON results next to P1 dir (../P3_auto_det.json)
    # ------------------------------------------------------------------
    out_path = p1_dir.parent.parent / "P3_auto_det.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("已保存完整结果至", out_path)


if __name__ == "__main__":
    main()
