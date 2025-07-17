#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图像预处理模块 - 用于古籍图像的预处理操作
包括：灰度化、二值化、倾斜校正等功能
"""

import cv2
import numpy as np
from typing import Tuple, Optional

from boocr.dataclasses import PageImage


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    将图像转换为灰度图

    Args:
        image: 输入图像（RGB或BGR格式）

    Returns:
        灰度图像
    """
    if len(image.shape) == 2:
        # 已经是灰度图
        return image

    # 转为灰度图
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def otsu_binarize(image: np.ndarray) -> np.ndarray:
    """
    使用Otsu算法对图像进行二值化

    Args:
        image: 输入灰度图像

    Returns:
        二值化后的图像
    """
    # 确保输入是灰度图
    gray_image = to_grayscale(image)

    # 应用Otsu二值化
    _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def detect_skew_angle(image: np.ndarray) -> float:
    """
    检测图像的倾斜角度

    Args:
        image: 输入图像（灰度图或二值图）

    Returns:
        检测到的倾斜角度（度数）
    """
    # 确保输入是灰度图
    gray = to_grayscale(image)

    # 对图像应用Canny边缘检测
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # 使用霍夫变换检测直线
    lines = cv2.HoughLinesP(edges, 1, np.pi/180,
                           threshold=100,
                           minLineLength=100,
                           maxLineGap=10)

    angles = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 避免除零错误
            if x2 - x1 != 0:
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                # 只考虑接近水平的线（对于竖排文字，水平线通常是更好的参考）
                if abs(angle) < 45:
                    angles.append(angle)

    # 如果找不到合适的线，返回0（不旋转）
    if not angles:
        return 0.0

    # 使用中位数来避免极端值的影响
    median_angle = np.median(angles)

    # 对于水平文本，倾斜校正角度应当是检测到角度的负值
    # 但由于我们处理的是竖排古籍，保持原值（因为旋转方向与排版方向有关）
    return median_angle


def deskew(image: np.ndarray, angle: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """
    图像倾斜校正

    Args:
        image: 输入图像
        angle: 可选的指定校正角度，如果为None则自动检测

    Returns:
        校正后的图像和检测到的角度
    """
    # 将图像转为灰度图
    gray = to_grayscale(image)

    if angle is None:
        # 自动检测倾斜角度
        detected_angle = detect_skew_angle(gray)
    else:
        detected_angle = angle

    # 获取图像中心点
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    # 旋转图像
    M = cv2.getRotationMatrix2D(center, detected_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)

    return rotated, detected_angle


def preprocess_image(page_image: PageImage,
                    deskew_angle: Optional[float] = None) -> PageImage:
    """
    对PageImage进行完整的预处理流程

    Args:
        page_image: 输入的PageImage对象
        deskew_angle: 可选的指定校正角度，如果为None则会进行自动检测

    Returns:
        预处理后的PageImage对象
    """
    # 灰度化
    gray_image = to_grayscale(page_image.image)

    # 先倾斜校正（在灰度图上完成以避免插值造成的伪影）
    rotated_gray, angle = deskew(gray_image, deskew_angle)

    # 再进行二值化，确保边缘清晰
    corrected_image = otsu_binarize(rotated_gray)

    # 创建新的PageImage对象
    processed_page = PageImage(
        page_index=page_image.page_index,
        image=corrected_image,
        width=corrected_image.shape[1],
        height=corrected_image.shape[0]
    )

    return processed_page
