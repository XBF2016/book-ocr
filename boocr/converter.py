#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
繁体到简体中文转换模块，基于opencc-py。
支持单行文本和多行文本的转换，保持转换前后文本结构一致。
"""

import logging
from typing import List, Tuple, Optional

import opencc

from boocr.dataclasses import OcrResult, RenderedPage

# 配置日志
logger = logging.getLogger(__name__)


class ChineseConverter:
    """繁体到简体中文转换器封装"""

    def __init__(self, config: str = 't2s'):
        """
        初始化转换器

        Args:
            config: OpenCC 转换配置，默认使用 't2s'（繁体到简体）
                可选值:
                - 't2s.json': 繁体到简体（默认）
                - 's2t.json': 简体到繁体
                - 't2tw.json': 繁体（中国大陆）到繁体（台湾）
                - 其他配置参见 OpenCC 文档
        """
        try:
            # opencc-python-reimplemented 期望配置名不带 .json 后缀，如果用户传入带后缀则剥离
            cfg_name = config
            if cfg_name.endswith('.json'):
                cfg_name = cfg_name[:-5]

            self.converter = opencc.OpenCC(cfg_name)
            logger.info(f"初始化中文转换器成功，使用配置: {config}")
            self.initialized = True
        except Exception as e:
            logger.error(f"初始化中文转换器失败: {e}")
            self.initialized = False
            raise RuntimeError(f"初始化中文转换器失败: {e}")

    def is_initialized(self) -> bool:
        """检查转换器是否已初始化"""
        return hasattr(self, 'initialized') and self.initialized

    def convert(self, text: str) -> str:
        """
        转换文本（繁体到简体）

        Args:
            text: 待转换的文本

        Returns:
            str: 转换后的文本
        """
        if not self.is_initialized():
            logger.error("转换器未初始化")
            return text

        try:
            converted = self.converter.convert(text)

            # 严格检查输入和输出的换行符数量是否一致（确保文本结构不变）
            if text.count('\n') != converted.count('\n'):
                logger.warning("转换前后换行符数量不一致，可能影响排版")

            return converted
        except Exception as e:
            logger.error(f"文本转换失败: {e}")
            return text

    def process_ocr_result(self, ocr_result: OcrResult) -> Tuple[str, str]:
        """
        处理OCR结果，返回原始繁体文本和转换后的简体文本

        Args:
            ocr_result: OCR识别结果

        Returns:
            Tuple[str, str]: (繁体文本, 简体文本)
        """
        trad_text = ocr_result.text
        simp_text = self.convert(trad_text)
        return trad_text, simp_text

    def process_ocr_results(self, ocr_results: List[OcrResult]) -> List[Tuple[str, str]]:
        """
        批量处理OCR结果

        Args:
            ocr_results: OCR结果列表

        Returns:
            List[Tuple[str, str]]: 包含(繁体文本, 简体文本)的列表
        """
        return [self.process_ocr_result(result) for result in ocr_results]


# 工厂方法：创建转换器实例
def create_converter(config: str = 't2s') -> ChineseConverter:
    """
    创建中文转换器实例

    Args:
        config: OpenCC 转换配置，默认为 't2s'（繁体到简体）

    Returns:
        ChineseConverter: 转换器实例
    """
    return ChineseConverter(config=config)


# 简单封装：直接转换文本
def convert_text(text: str, config: str = 't2s') -> str:
    """
    将文本从繁体转换为简体

    Args:
        text: 待转换的文本
        config: OpenCC 转换配置，默认为 't2s'（繁体到简体）

    Returns:
        str: 转换后的文本
    """
    try:
        converter = create_converter(config)
        return converter.convert(text)
    except Exception as e:
        logger.error(f"文本转换失败: {e}")
        return text
