#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试竖排PDF排版功能。
"""
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

from boocr.dataclasses import RenderedPage, RenderConfig
from boocr.composer import PdfComposer, create_pdf_composer, create_simplified_pdf

# 测试数据
TEST_TEXT_SIMPLIFIED = "这是简体中文测试"
TEST_TEXT_TRADITIONAL = "這是繁體中文測試"


@pytest.fixture
def test_font_path():
    """返回测试用字体路径"""
    # 使用系统自带的字体，Windows和Linux通用选择
    if os.name == 'nt':  # Windows
        font_path = "C:/Windows/Fonts/simhei.ttf"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/simsun.ttc"  # 备选
    else:  # Linux/Unix
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        if not os.path.exists(font_path):
            # 使用内置字体作为后备
            font_path = "Helvetica"

    return font_path


@pytest.fixture
def test_rendered_page():
    """创建测试用的渲染页面对象"""
    return RenderedPage(
        page_index=0,
        page_size=(595.0, 842.0),  # A4 size in points
        trad_texts=[TEST_TEXT_TRADITIONAL, TEST_TEXT_TRADITIONAL],  # 两列繁体文本
        simp_texts=[TEST_TEXT_SIMPLIFIED, TEST_TEXT_SIMPLIFIED],    # 两列简体文本
        column_bboxes=[(50, 50, 250, 750), (350, 50, 550, 750)]    # 两列区域
    )


def test_pdf_composer_initialization(test_font_path):
    """测试PDF排版器初始化"""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output.pdf"
        config = RenderConfig(
            output_path=output_path,
            font_path=test_font_path,
            font_size=16,
            line_spacing_ratio=1.5
        )

        composer = PdfComposer(config)
        assert composer.initialized
        assert composer.font_name is not None
        assert composer.config.font_size == 16


def test_create_pdf_composer(test_font_path):
    """测试创建PDF排版器工厂方法"""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output.pdf"
        config = RenderConfig(
            output_path=output_path,
            font_path=test_font_path
        )

        composer = create_pdf_composer(config)
        assert isinstance(composer, PdfComposer)
        assert composer.initialized


def test_render_page(test_font_path, test_rendered_page):
    """测试单页渲染"""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_page.pdf"
        config = RenderConfig(
            output_path=output_path,
            font_path=test_font_path
        )

        composer = PdfComposer(config)
        composer.render_page(test_rendered_page)

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_render_pages(test_font_path, test_rendered_page):
    """测试多页渲染"""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_pages.pdf"
        config = RenderConfig(
            output_path=output_path,
            font_path=test_font_path
        )

        composer = PdfComposer(config)
        result_path = composer.render_pages([test_rendered_page, test_rendered_page])

        # 验证文件已创建并返回路径一致
        assert result_path.exists()
        assert result_path == output_path
        assert output_path.stat().st_size > 0


def test_create_simplified_pdf(test_font_path, test_rendered_page):
    """测试创建简体PDF的便捷函数"""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_simplified.pdf"

        result_path = create_simplified_pdf(
            pages=[test_rendered_page],
            output_path=output_path,
            font_path=test_font_path,
            font_size=14,
            line_spacing_ratio=1.3
        )

        # 验证文件已创建并返回路径一致
        assert result_path.exists()
        assert result_path == output_path
        assert output_path.stat().st_size > 0
