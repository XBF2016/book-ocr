"""
PDF处理工具模块。

提供PDF文件解析、页面提取和光栅化等功能。
"""

import numpy as np
from PIL import Image
import pdfplumber
from pathlib import Path
import io

from boocr.dataclasses import InputSource, PageImage


def extract_pages_from_pdf(pdf_path: str | Path) -> list[PageImage]:
    """
    从PDF文件中提取所有页面，并转换为PageImage对象列表。

    Args:
        pdf_path: PDF文件路径

    Returns:
        list[PageImage]: 页面图像对象列表
    """
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF文件未找到: {pdf_path}")

    page_images = []

    # 使用pdfplumber打开PDF文件
    with pdfplumber.open(pdf_path) as pdf:
        # 处理每一页
        for i, page in enumerate(pdf.pages):
            # 获取页面尺寸
            width = int(page.width * 3)  # 放大3倍以提高分辨率
            height = int(page.height * 3)

            # 将页面渲染为图像
            img = page.to_image(resolution=300)  # 300 DPI分辨率
            img_data = img.original

            # 转换为numpy数组
            page_array = pdf_to_ndarray(img_data)

            # 创建并添加PageImage对象
            page_image = PageImage(
                page_index=i,
                image=page_array,
                width=width,
                height=height
            )
            page_images.append(page_image)

    return page_images


def pdf_to_ndarray(pdf_page) -> np.ndarray:
    """
    将PDF页面转换为numpy ndarray格式的图像。

    Args:
        pdf_page: PDF页面图像对象（PIL Image）

    Returns:
        np.ndarray: 表示图像的numpy数组，格式为(H, W, C) RGB
    """
    if isinstance(pdf_page, Image.Image):
        # 如果输入已经是PIL图像，直接转换为numpy数组
        img_pil = pdf_page
    else:
        # 否则假定它是pdfplumber页面图像的内部表示
        # 转换为PIL图像对象
        img_pil = Image.open(io.BytesIO(pdf_page))

    # 确保图像是RGB模式
    if img_pil.mode != 'RGB':
        img_pil = img_pil.convert('RGB')

    # 转换为numpy数组
    img_array = np.array(img_pil)

    return img_array
