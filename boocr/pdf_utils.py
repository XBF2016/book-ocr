"""
PDF处理工具模块。

提供PDF文件解析、页面提取和光栅化等功能。
"""

import numpy as np
from PIL import Image
import pdfplumber
from pathlib import Path

from boocr.dataclasses import InputSource, PageImage


def extract_pages_from_pdf(pdf_path: str | Path) -> list[PageImage]:
    """
    从PDF文件中提取所有页面，并转换为PageImage对象列表。

    Args:
        pdf_path: PDF文件路径

    Returns:
        list[PageImage]: 页面图像对象列表
    """
    # TODO: 实现PDF拆页与光栅化逻辑
    pass


def pdf_to_ndarray(pdf_page) -> np.ndarray:
    """
    将PDF页面转换为numpy ndarray格式的图像。

    Args:
        pdf_page: PDF页面对象

    Returns:
        np.ndarray: 表示图像的numpy数组
    """
    # TODO: 实现PDF页面到numpy数组的转换
    pass
