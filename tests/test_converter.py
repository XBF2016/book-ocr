#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
繁体到简体转换模块的单元测试。
"""

import pytest
from boocr.converter import convert_text, create_converter, ChineseConverter
from boocr.dataclasses import OcrResult


class TestChineseConverter:
    """测试中文繁简转换功能"""

    def test_converter_initialization(self):
        """测试转换器初始化"""
        converter = create_converter()
        assert converter.is_initialized()
        assert isinstance(converter, ChineseConverter)

    def test_simple_conversion(self):
        """测试简单的繁体到简体转换"""
        # 繁体文本
        trad_text = "這是繁體中文"
        # 期望的简体文本
        simp_text = "这是繁体中文"

        # 使用封装函数直接转换
        converted = convert_text(trad_text)
        assert converted == simp_text

    def test_multiline_conversion(self):
        """测试多行文本的转换，确保保持换行符结构一致"""
        # 多行繁体文本
        trad_text = "這是第一行\n這是第二行\n這是第三行"
        # 期望的多行简体文本
        simp_text = "这是第一行\n这是第二行\n这是第三行"

        # 创建转换器并转换
        converter = create_converter()
        converted = converter.convert(trad_text)

        # 断言转换结果
        assert converted == simp_text
        assert converted.count('\n') == trad_text.count('\n')  # 确保换行符数量一致

    def test_complex_text_conversion(self):
        """测试包含各种字符的复杂文本转换"""
        # 包含数字、标点和特殊字符的繁体文本
        trad_text = "繁體中文 123!@#$%^&*()_+，。？「」『』"
        # 期望的简体文本
        simp_text = "繁体中文 123!@#$%^&*()_+，。？「」『』"

        converter = create_converter()
        converted = converter.convert(trad_text)
        assert converted == simp_text

    def test_empty_text_conversion(self):
        """测试空文本的转换"""
        empty_text = ""
        converter = create_converter()
        converted = converter.convert(empty_text)
        assert converted == empty_text

    def test_process_ocr_result(self):
        """测试处理OCR结果"""
        # 创建一个OcrResult对象
        ocr_result = OcrResult(
            page_index=0,
            column_index=1,
            text="這是繁體中文OCR結果",
            confidence=0.95
        )

        # 期望的简体文本
        expected_simp = "这是繁体中文OCR结果"

        # 处理OCR结果
        converter = create_converter()
        trad_text, simp_text = converter.process_ocr_result(ocr_result)

        # 断言结果
        assert trad_text == ocr_result.text
        assert simp_text == expected_simp

    def test_process_ocr_results_batch(self):
        """测试批量处理OCR结果"""
        # 创建多个OcrResult对象
        ocr_results = [
            OcrResult(page_index=0, column_index=0, text="第一列繁體", confidence=0.9),
            OcrResult(page_index=0, column_index=1, text="第二列繁體", confidence=0.8),
            OcrResult(page_index=0, column_index=2, text="第三列繁體", confidence=0.7)
        ]

        # 期望的简体文本
        expected_simp = ["第一列繁体", "第二列繁体", "第三列繁体"]

        # 批量处理
        converter = create_converter()
        results = converter.process_ocr_results(ocr_results)

        # 断言结果
        assert len(results) == len(ocr_results)
        for i, (trad, simp) in enumerate(results):
            assert trad == ocr_results[i].text
            assert simp == expected_simp[i]
