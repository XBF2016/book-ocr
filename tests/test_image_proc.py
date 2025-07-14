#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图像处理模块中的函数
"""

import cv2
import numpy as np
import pytest

from boocr.image_proc import to_grayscale, otsu_binarize, preprocess_image
from boocr.dataclasses import PageImage


def test_to_grayscale():
    """测试灰度化函数"""
    # 创建彩色测试图像（RGB）
    color_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    color_image[30:70, 30:70, :] = [200, 100, 50]  # 中间区域设置不同颜色

    # 转换为灰度图
    gray_image = to_grayscale(color_image)

    # 验证转换后的图像是灰度图
    assert len(gray_image.shape) == 2
    assert gray_image.shape == (100, 100)

    # 验证当输入已经是灰度图时，函数能正确处理
    gray_image2 = to_grayscale(gray_image)
    assert gray_image2.shape == gray_image.shape
    assert np.array_equal(gray_image, gray_image2)


def test_otsu_binarize():
    """测试Otsu二值化函数"""
    # 创建灰度测试图像
    gray_image = np.zeros((100, 100), dtype=np.uint8)
    gray_image[30:70, 30:70] = 200  # 中间区域设置不同亮度

    # 二值化
    binary_image = otsu_binarize(gray_image)

    # 验证结果是二值化的（只包含0和255的值）
    assert set(np.unique(binary_image)).issubset({0, 255})

    # 验证二值化后深色区域是黑色(0)，浅色区域是白色(255)
    assert np.all(binary_image[0:30, 0:30] == 0)
    assert np.all(binary_image[40:60, 40:60] == 255)

    # 测试彩色输入的情况
    color_image = np.zeros((100, 100, 3), dtype=np.uint8)
    color_image[30:70, 30:70, :] = 200
    binary_color = otsu_binarize(color_image)
    assert set(np.unique(binary_color)).issubset({0, 255})


def test_preprocess_image():
    """测试图像预处理流程"""
    # 创建测试用PageImage
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[30:70, 30:70, :] = 200

    page_img = PageImage(
        page_num=0,
        image=test_image,
        width=100,
        height=100
    )

    # 执行预处理
    processed_page = preprocess_image(page_img)

    # 验证结果
    assert processed_page.page_num == page_img.page_num
    assert processed_page.width == page_img.width
    assert processed_page.height == page_img.height
    assert set(np.unique(processed_page.image)).issubset({0, 255})  # 二值化结果
