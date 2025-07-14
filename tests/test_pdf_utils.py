"""
测试PDF处理工具模块的功能。
"""
import os
import pytest
import numpy as np
from PIL import Image
import tempfile
from pathlib import Path

from boocr.pdf_utils import extract_pages_from_pdf, pdf_to_ndarray
from boocr.dataclasses import PageImage


def create_test_pdf():
    """创建一个简单的测试PDF文件。"""
    import reportlab.pdfgen.canvas

    # 创建临时PDF文件
    pdf_path = tempfile.mktemp(suffix='.pdf')
    c = reportlab.pdfgen.canvas.Canvas(pdf_path)

    # 添加两页
    for i in range(2):
        c.drawString(100, 100, f"测试页面 {i+1}")
        c.showPage()

    c.save()
    return pdf_path


def test_pdf_to_ndarray():
    """测试PDF页面转numpy数组功能。"""
    # 创建一个简单的PIL图像用于测试
    img = Image.new('RGB', (100, 100), color='red')

    # 转换为numpy数组
    img_array = pdf_to_ndarray(img)

    # 验证结果
    assert isinstance(img_array, np.ndarray)
    assert img_array.shape == (100, 100, 3)  # (H, W, 3) 格式
    assert img_array.dtype == np.uint8
    assert np.all(img_array[:, :, 0] == 255)  # 红色通道全255
    assert np.all(img_array[:, :, 1] == 0)    # 绿色通道全0
    assert np.all(img_array[:, :, 2] == 0)    # 蓝色通道全0


def test_extract_pages_from_pdf():
    """测试PDF文件提取页面功能。"""
    # 创建测试PDF
    pdf_path = create_test_pdf()

    try:
        # 提取页面
        page_images = extract_pages_from_pdf(pdf_path)

        # 验证结果
        assert len(page_images) == 2  # 应该有两页

        for i, page_image in enumerate(page_images):
            assert page_image.page_index == i
            assert isinstance(page_image.image, np.ndarray)
            assert page_image.image.ndim == 3  # (H, W, 3) 格式
            assert page_image.width > 0
            assert page_image.height > 0

    finally:
        # 清理临时文件
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def test_extract_pages_from_pdf_with_path_object():
    """测试使用Path对象作为输入时PDF文件提取页面功能。"""
    # 创建测试PDF
    pdf_path = create_test_pdf()

    try:
        # 将路径转换为Path对象
        pdf_path_obj = Path(pdf_path)

        # 提取页面
        page_images = extract_pages_from_pdf(pdf_path_obj)

        # 验证结果
        assert len(page_images) == 2  # 应该有两页

        # 验证返回的是PageImage对象列表
        assert all(isinstance(page, PageImage) for page in page_images)

    finally:
        # 清理临时文件
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def test_page_image_attributes():
    """测试PageImage对象的属性和完整性。"""
    # 创建测试PDF
    pdf_path = create_test_pdf()

    try:
        # 提取页面
        page_images = extract_pages_from_pdf(pdf_path)

        # 详细验证PageImage对象
        for i, page_image in enumerate(page_images):
            # 验证是PageImage类的实例
            assert isinstance(page_image, PageImage)

            # 验证页码索引正确
            assert page_image.page_index == i

            # 验证图像数据
            assert isinstance(page_image.image, np.ndarray)
            assert page_image.image.ndim == 3  # 3维数组(高,宽,通道)
            assert page_image.image.shape[2] == 3  # RGB三通道

            # 验证宽高是有效的正数值（但不必等于图像尺寸）
            # 在pdf_utils.py中，width和height是原始PDF页面的尺寸，经过缩放后不等于图像数组的实际尺寸
            assert page_image.width > 0
            assert page_image.height > 0

            # 验证图像数据有效（非全零）
            assert np.sum(page_image.image) > 0

            # 验证图像数据类型正确
            assert page_image.image.dtype == np.uint8

    finally:
        # 清理临时文件
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def test_extract_pages_from_nonexistent_pdf():
    """测试处理不存在的PDF文件。"""
    non_existent_path = Path("/path/to/nonexistent.pdf")

    # 应该抛出FileNotFoundError异常
    with pytest.raises(FileNotFoundError):
        extract_pages_from_pdf(non_existent_path)
