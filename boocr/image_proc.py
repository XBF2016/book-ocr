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

    detected_angle = 0.0
    if angle is None:
        # TODO: 实现自动倾斜角度检测
        # 这里将在T14任务中实现
        pass
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
        deskew_angle: 可选的指定校正角度

    Returns:
        预处理后的PageImage对象
    """
    # 灰度化
    gray_image = to_grayscale(page_image.image)

    # 二值化
    binary_image = otsu_binarize(gray_image)

    # 倾斜校正（如果指定了角度）
    if deskew_angle is not None:
        corrected_image, _ = deskew(binary_image, deskew_angle)
    else:
        corrected_image = binary_image

    # 创建新的PageImage对象
    processed_page = PageImage(
        page_num=page_image.page_num,
        image=corrected_image,
        width=corrected_image.shape[1],
        height=corrected_image.shape[0]
    )

    return processed_page
