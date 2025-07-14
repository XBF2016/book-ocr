from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np


# P0: Input
@dataclass
class InputSource:
    """
    输入源。目前仅支持本地 PDF 文件路径。
    """
    pdf_path: Path


# P0 -> P1: PDF Rasterization Output
@dataclass
class PageImage:
    """
    PDF 单页光栅化后的图像。
    """
    page_index: int  # 0-based page index from original PDF
    image: np.ndarray  # Image data as a numpy array (H, W, C) in RGB format
    width: int  # Original page width in pixels
    height: int  # Original page height in pixels


# P1 -> P2: Column Detection Output
@dataclass
class ColumnCrop:
    """
    从页面图像中裁切出的单列图像。
    """
    page_index: int
    column_index: int
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) relative to page
    image: np.ndarray  # Image data for the column crop


# P2 -> P3: OCR Output
@dataclass
class OcrResult:
    """
    单列图像的 OCR 识别结果（繁体）。
    """
    page_index: int
    column_index: int
    text: str
    confidence: float  # Average confidence for the text block


# P4/P5: Rendering Input
@dataclass
class RenderedPage:
    """
    用于渲染输出的单页数据。
    包含简体和繁体文本以及其在页面上的位置信息。
    """
    page_index: int
    page_size: Tuple[float, float]  # (width, height) in points
    trad_texts: List[str]  # List of traditional text columns
    simp_texts: List[str]  # List of simplified text columns
    column_bboxes: List[Tuple[int, int, int, int]]  # Bboxes for each column


# Pipeline Configuration
@dataclass
class RenderConfig:
    """
    渲染输出 PDF 的配置。
    """
    output_path: Path
    font_path: str  # Path to a font file that supports Chinese characters
    font_size: int = 12
    line_spacing_ratio: float = 1.5
