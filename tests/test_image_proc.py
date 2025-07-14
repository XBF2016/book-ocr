#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图像处理模块中的函数
"""

import cv2
import numpy as np
import pytest

from boocr.image_proc import to_grayscale, otsu_binarize, preprocess_image, deskew, detect_skew_angle
from boocr.dataclasses import PageImage


def create_test_image(path, h, w, angle_deg=0):
    """辅助函数：创建并保存一张用于测试的倾斜图像"""
    img = np.zeros((h, w), dtype=np.uint8)
    center = (w // 2, h // 2)

    # 绘制一条倾斜的线
    length = min(h, w) // 2
    radian = np.deg2rad(angle_deg)
    x1 = int(center[0] - length * np.cos(radian))
    y1 = int(center[1] - length * np.sin(radian))
    x2 = int(center[0] + length * np.cos(radian))
    y2 = int(center[1] + length * np.sin(radian))
    cv2.line(img, (x1, y1), (x2, y2), 255, 5)

    cv2.imwrite(str(path), img)
    return img


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


def test_deskew():
    """测试倾斜校正功能"""
    # 创建倾斜的测试图像（包含一条倾斜的线）
    img = np.zeros((200, 200), dtype=np.uint8)

    # 绘制一条倾斜10度的线
    angle_deg = 10
    center = (100, 100)
    length = 80

    # 计算线条的端点
    radian = np.deg2rad(angle_deg)
    x1 = int(center[0] - length * np.cos(radian))
    y1 = int(center[1] - length * np.sin(radian))
    x2 = int(center[0] + length * np.cos(radian))
    y2 = int(center[1] + length * np.sin(radian))

    # 绘制线条
    cv2.line(img, (x1, y1), (x2, y2), 255, 5)

    # 自动检测倾斜角度
    detected_angle = detect_skew_angle(img)

    # 角度检测应该接近10度（允许±5度的误差）
    assert abs(detected_angle - angle_deg) < 5

    # 测试指定角度的倾斜校正
    corrected_img, angle = deskew(img, angle=angle_deg)
    assert angle == angle_deg
    # 校正后图像尺寸不变
    assert corrected_img.shape == img.shape

    # 测试自动检测角度的倾斜校正
    corrected_img, detected = deskew(img)
    # 检测到的角度应该接近我们设定的角度
    assert abs(detected - angle_deg) < 5
    # 校正后图像尺寸不变
    assert corrected_img.shape == img.shape


def test_preprocess_image():
    """测试图像预处理流程"""
    # 创建测试用PageImage
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[30:70, 30:70, :] = 200

    page_img = PageImage(
        page_index=0,
        image=test_image,
        width=100,
        height=100
    )

    # 执行预处理（不指定角度）
    processed_page = preprocess_image(page_img)

    # 验证结果
    assert processed_page.page_index == page_img.page_index
    assert processed_page.width == page_img.width
    assert processed_page.height == page_img.height
    assert set(np.unique(processed_page.image)).issubset({0, 255})  # 二值化结果

    # 测试指定角度的预处理
    processed_page2 = preprocess_image(page_img, deskew_angle=5.0)
    assert processed_page2.page_index == page_img.page_index
    assert processed_page2.width == page_img.width
    assert processed_page2.height == page_img.height


def test_preprocess_image_from_file(tmp_path):
    """
    测试从文件读取图像->预处理->断言返回shape
    这对应于T15的要求
    """
    # 1. 准备测试图片
    h, w = 300, 400
    test_image_path = tmp_path / "test_image.png"
    create_test_image(test_image_path, h, w, angle_deg=0)

    # 2. 从文件读取示例图
    loaded_image = cv2.imread(str(test_image_path), cv2.IMREAD_COLOR)
    assert loaded_image is not None
    assert loaded_image.shape == (h, w, 3)

    # 3. 封装为 PageImage 并执行预处理
    page_img = PageImage(page_index=0, image=loaded_image, width=w, height=h)
    processed_page = preprocess_image(page_img, deskew_angle=0)

    # 4. 断言返回 ndarray shape
    # 预处理后，图像尺寸应保持不变
    assert processed_page.image.shape == (h, w)
    assert processed_page.width == w
    assert processed_page.height == h
