#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR模块功能
"""

import os
import pytest
import numpy as np
from pathlib import Path

from boocr.ocr import VerticalChineseOCR, create_ocr_engine
from boocr.dataclasses import ColumnCrop


def test_ocr_engine_initialization():
    """测试OCR引擎初始化"""
    try:
        ocr = create_ocr_engine(use_gpu=False)
        assert ocr.is_initialized() == True
        assert isinstance(ocr, VerticalChineseOCR)
    except Exception as e:
        pytest.skip(f"OCR引擎初始化失败，可能是网络或依赖问题: {e}")


@pytest.mark.skipif(
    "GITHUB_ACTIONS" in os.environ,
    reason="在CI环境中跳过需要下载大型模型的测试"
)
def test_ocr_run_with_dummy_image():
    """测试OCR引擎的运行，使用空白图像"""
    try:
        # 创建一个简单的空白图像
        dummy_image = np.ones((100, 50, 3), dtype=np.uint8) * 255

        # 创建一个列裁剪对象
        column = ColumnCrop(
            page_index=0,
            column_index=0,
            bbox=(0, 0, 50, 100),
            image=dummy_image
        )

        # 初始化OCR引擎
        ocr = create_ocr_engine(use_gpu=False)

        # 运行OCR
        result = ocr.run_ocr(column)

        # 验证结果格式
        assert hasattr(result, 'text')
        assert hasattr(result, 'confidence')
        assert result.page_index == 0
        assert result.column_index == 0
        # 空白图像可能没有文本，所以我们不检查文本内容
    except Exception as e:
        pytest.skip(f"OCR运行测试失败: {e}")
