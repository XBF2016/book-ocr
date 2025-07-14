#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR module for vertical Chinese text recognition using PaddleOCR.
Support for traditional Chinese characters with vertical layout.
"""

import os
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any

# PaddleOCR相关导入
from paddleocr import PaddleOCR

# Import project specific modules
from boocr.dataclasses import ColumnCrop, OcrResult
from boocr.ocr_model import ensure_models_ready, ModelManager

# 配置日志
logger = logging.getLogger(__name__)


class VerticalChineseOCR:
    """
    竖排繁体中文OCR引擎封装，基于PaddleOCR。
    """
    def __init__(
        self,
        use_gpu: bool = False,
        gpu_mem: int = 500,
        enable_mkldnn: bool = True,
        cpu_threads: int = 4,
        lang_type: str = "chinese_cht",  # 繁体中文模型
        auto_download: bool = True,      # 自动下载模型
    ):
        """
        初始化OCR引擎

        Args:
            use_gpu: 是否使用GPU
            gpu_mem: GPU内存大小(MB)
            enable_mkldnn: 是否启用mkldnn加速
            cpu_threads: CPU线程数
            lang_type: 语言类型，默认为繁体中文(chinese_cht)
            auto_download: 是否自动下载模型（如果不存在）
        """
        logger.info(f"初始化竖排繁体OCR引擎，使用语言模型: {lang_type}")

        # 如果自动下载模型开关打开，确保模型已下载
        if auto_download:
            self._ensure_models()

        try:
            self.ocr = PaddleOCR(
                # 竖排模式
                rec_algorithm="CRNN",
                det=True,  # 启用文本检测
                rec=True,  # 启用文本识别
                cls=True,  # 启用文本方向分类
                lang=lang_type,  # 使用繁体中文模型
                use_angle_cls=True,  # 使用文字方向分类器
                # 性能相关配置
                use_gpu=use_gpu,
                gpu_mem=gpu_mem,
                enable_mkldnn=enable_mkldnn,
                cpu_threads=cpu_threads,
                # 繁体中文配置
                rec_char_dict_path=None,  # 使用默认字典
                det_db_thresh=0.3,  # 检测阈值
                det_db_box_thresh=0.5,  # 检测框阈值
                det_db_unclip_ratio=1.6,  # 检测框大小
                # 竖排配置 - 模型将自动下载
                cls_model_dir=None,  # 使用默认方向分类器
                det_model_dir=None,  # 使用默认检测模型
                rec_model_dir=None,  # 使用默认识别模型
                # 其他配置
                show_log=False,  # 不显示详细日志
            )
            self.initialized = True
            logger.info("OCR引擎初始化成功")
        except Exception as e:
            logger.error(f"OCR引擎初始化失败: {e}")
            self.initialized = False
            raise RuntimeError(f"OCR引擎初始化失败: {e}")

    def _ensure_models(self):
        """确保所需的模型已经下载并准备就绪"""
        logger.info("检查 PaddleOCR 模型...")

        try:
            # 使用我们的自定义下载器确保模型已准备就绪
            models_ready = ensure_models_ready()
            if not models_ready:
                logger.warning("一个或多个模型下载失败，PaddleOCR 可能会尝试自动下载")
            else:
                logger.info("所有模型已准备就绪")
        except Exception as e:
            logger.error(f"模型检查失败: {e}")
            logger.warning("将使用 PaddleOCR 内置下载流程")

    def is_initialized(self) -> bool:
        """检查OCR引擎是否已初始化"""
        return hasattr(self, 'initialized') and self.initialized

    def run_ocr(self, column_crop: ColumnCrop) -> OcrResult:
        """
        对裁剪的列图像执行OCR识别

        Args:
            column_crop: 从页面裁剪的单列图像

        Returns:
            OcrResult: OCR识别结果，包含识别的文本和置信度
        """
        if not self.is_initialized():
            raise RuntimeError("OCR引擎未初始化")

        # 执行OCR
        try:
            result = self.ocr.ocr(column_crop.image, cls=True)

            # 处理OCR结果
            if not result or len(result) == 0 or not result[0]:
                logger.warning(f"页面 {column_crop.page_index} 列 {column_crop.column_index} OCR未识别到文本")
                return OcrResult(
                    page_index=column_crop.page_index,
                    column_index=column_crop.column_index,
                    text="",
                    confidence=0.0
                )

            # 组装文本和计算置信度
            texts = []
            confidences = []

            # PaddleOCR的结果格式: [[[文本框坐标], [文本, 置信度]], [...]]
            for line in result[0]:
                if len(line) >= 2 and isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                    text, confidence = line[1]
                    texts.append(text)
                    confidences.append(float(confidence))

            # 垂直文本，自下而上连接（考虑竖排从右到左的阅读顺序）
            full_text = "\n".join(reversed(texts))
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return OcrResult(
                page_index=column_crop.page_index,
                column_index=column_crop.column_index,
                text=full_text,
                confidence=avg_confidence
            )
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return OcrResult(
                page_index=column_crop.page_index,
                column_index=column_crop.column_index,
                text="",
                confidence=0.0
            )

    def process_columns(self, columns: List[ColumnCrop]) -> List[OcrResult]:
        """
        批量处理多个列图像

        Args:
            columns: 列图像列表

        Returns:
            List[OcrResult]: OCR识别结果列表
        """
        results = []
        for column in columns:
            try:
                result = self.run_ocr(column)
                results.append(result)
            except Exception as e:
                logger.error(f"处理列 {column.page_index}-{column.column_index} 失败: {e}")
                # 添加空结果以保持索引一致性
                results.append(OcrResult(
                    page_index=column.page_index,
                    column_index=column.column_index,
                    text="",
                    confidence=0.0
                ))

        return results


# 工厂方法：创建OCR引擎实例
def create_ocr_engine(use_gpu: bool = False, auto_download: bool = True) -> VerticalChineseOCR:
    """
    创建竖排繁体中文OCR引擎实例

    Args:
        use_gpu: 是否使用GPU加速
        auto_download: 是否自动下载模型（如果不存在）

    Returns:
        VerticalChineseOCR: OCR引擎实例
    """
    return VerticalChineseOCR(
        use_gpu=use_gpu,
        lang_type="chinese_cht",  # 使用繁体中文模型
        auto_download=auto_download,
    )
