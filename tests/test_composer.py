#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试竖排PDF排版功能。
"""
import os
from pathlib import Path

import pytest
import pdfplumber
from reportlab.lib.pagesizes import A4

from boocr.dataclasses import RenderedPage, RenderConfig
from boocr.composer import PdfComposer, create_simplified_pdf

# 测试数据
TEST_TEXT_SIMPLIFIED = "这是简体中文测试"
TEST_TEXT_TRADITIONAL = "這是繁體中文測試"


@pytest.fixture
def test_font_path() -> str:
    """
    返回一个可用的中文字体路径，用于测试。
    在Windows上查找'simhei.ttf'或'simsun.ttc'，在其他系统上则会失败，
    因为我们不能假设CI/Unix环境中有特定的中文字体。
    如果找不到字体，测试将跳过。
    """
    if os.name == 'nt':  # Windows
        font_paths_to_check = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        for font_path in font_paths_to_check:
            if os.path.exists(font_path):
                return font_path

    # 在非Windows环境下或未找到字体时，跳过测试
    pytest.skip("无法在当前测试环境中找到合适的中文字体，跳过PDF生成测试。")
    return "" # 为类型检查提供返回值


@pytest.fixture
def test_rendered_page() -> RenderedPage:
    """创建测试用的单页渲染数据对象"""
    return RenderedPage(
        page_index=0,
        page_size=A4,  # (595.27, 841.89)
        trad_texts=[TEST_TEXT_TRADITIONAL, TEST_TEXT_TRADITIONAL],
        simp_texts=[TEST_TEXT_SIMPLIFIED, TEST_TEXT_SIMPLIFIED],
        column_bboxes=[(50, 100, 100, 700), (150, 100, 200, 700)]
    )


@pytest.fixture
def temp_output_pdf(tmp_path: Path) -> Path:
    """提供一个临时的PDF输出路径"""
    return tmp_path / "test_output.pdf"


def test_pdf_composer_initialization(test_font_path: str, temp_output_pdf: Path):
    """测试PdfComposer初始化"""
    config = RenderConfig(
        output_path=temp_output_pdf,
        font_path=test_font_path,
        font_size=16,
        line_spacing_ratio=1.5
    )
    composer = PdfComposer(config)
    assert composer.initialized
    assert composer.font_name is not None
    assert composer.config.font_size == 16


def test_render_pages(test_font_path: str, test_rendered_page: RenderedPage, temp_output_pdf: Path):
    """测试 render_pages 方法能够成功生成PDF"""
    config = RenderConfig(output_path=temp_output_pdf, font_path=test_font_path)
    composer = PdfComposer(config)

    # 测试单页
    result_path = composer.render_pages([test_rendered_page])
    assert result_path.exists()
    assert result_path == temp_output_pdf
    assert temp_output_pdf.stat().st_size > 0

    # 测试多页
    multi_page_output = temp_output_pdf.with_name("multi_page.pdf")
    config.output_path = multi_page_output
    composer = PdfComposer(config)
    result_path = composer.render_pages([test_rendered_page, test_rendered_page])
    assert result_path.exists()
    assert result_path.stat().st_size > temp_output_pdf.stat().st_size


def test_create_simplified_pdf_and_assert_parsable(
    test_font_path: str, test_rendered_page: RenderedPage, temp_output_pdf: Path
):
    """
    测试 create_simplified_pdf 便捷函数，并断言生成的PDF文件可被解析且内容正确。
    """
    result_path = create_simplified_pdf(
        pages=[test_rendered_page],
        output_path=temp_output_pdf,
        font_path=test_font_path,
    )

    # 1. 验证文件已创建
    assert result_path.exists()
    assert result_path == temp_output_pdf
    assert temp_output_pdf.stat().st_size > 0

    # 2. 验证文件可解析且内容正确
    with pdfplumber.open(result_path) as pdf:
        assert len(pdf.pages) == 1, "PDF页数应为1"

        # 使用 .chars 提取字符级信息，因为 drawString 逐字绘制，extract_text 可能无法正确组合
        page_chars = pdf.pages[0].chars
        extracted_text = "".join([c['text'] for c in page_chars])

        # pdfplumber 提取竖排文本时可能会有空格或换行，使用 `in` 来模糊匹配
        # 移除空格进行更可靠的断言
        assert TEST_TEXT_SIMPLIFIED in extracted_text.replace(" ", ""), "PDF中应包含指定的简体测试文本"
