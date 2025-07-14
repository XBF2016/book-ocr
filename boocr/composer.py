#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竖排排版模块，用于根据OCR结果生成竖排文本的PDF。

使用 reportlab 库绘制竖排简体文字，确保生成的PDF中文字可搜索。
支持根据 RenderedPage 对象生成包含竖排文本的PDF页面。
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate

from boocr.dataclasses import RenderedPage, RenderConfig

# 配置日志
logger = logging.getLogger(__name__)


class PdfComposer:
    """竖排PDF排版器"""

    def __init__(self, config: RenderConfig):
        """
        初始化PDF排版器

        Args:
            config: 渲染配置
        """
        self.config = config
        self._initialize_fonts()
        self.initialized = True
        logger.info(f"初始化PDF排版器成功，输出路径: {config.output_path}")

    def _initialize_fonts(self):
        """初始化字体"""
        try:
            # 注册字体，使用配置中提供的字体路径
            font_name = "ChineseFont"
            pdfmetrics.registerFont(TTFont(font_name, self.config.font_path))
            self.font_name = font_name
            logger.info(f"成功注册字体: {self.config.font_path}")
        except Exception as e:
            logger.error(f"字体初始化失败: {e}")
            # 如果配置的字体失败，尝试使用系统默认字体
            self.font_name = "Helvetica"  # 默认字体
            logger.warning(f"将使用默认字体: {self.font_name}")

    def create_vertical_text(
        self,
        canvas_obj: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        font_name: str = None,
        font_size: int = None,
        line_spacing: float = None
    ):
        """
        在Canvas上创建竖排文本

        Args:
            canvas_obj: ReportLab Canvas对象
            text: 要绘制的文本
            x: 文本左上角x坐标
            y: 文本左上角y坐标
            font_name: 字体名称，如未提供则使用配置中的字体
            font_size: 字体大小，如未提供则使用配置中的字体大小
            line_spacing: 行间距倍数，如未提供则使用配置中的行间距
        """
        if font_name is None:
            font_name = self.font_name
        if font_size is None:
            font_size = self.config.font_size
        if line_spacing is None:
            line_spacing = self.config.line_spacing_ratio

        canvas_obj.saveState()
        canvas_obj.setFont(font_name, font_size)

        # 分割为单字符进行竖排绘制
        char_height = font_size * line_spacing
        current_y = y
        current_x = x

        # 处理多行文本（按列绘制）
        for line in text.split('\n'):
            # 如果是空行，则只增加一个字符的间距
            if not line:
                current_x += char_height
                continue

            # 逐字绘制
            for char in line:
                canvas_obj.drawString(current_x, current_y, char)
                current_y -= font_size  # 向下移动一个字符高度

            # 下一列
            current_x += char_height
            current_y = y  # 重置y坐标到顶部

        canvas_obj.restoreState()

    def render_page(self, page: RenderedPage) -> None:
        """
        渲染单个页面到PDF

        Args:
            page: 要渲染的页面对象
        """
        try:
            # 创建一个单页的Canvas
            page_size = page.page_size
            page_width, page_height = page_size

            # 如果输出文件夹不存在，则创建
            output_dir = self.config.output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # 创建或追加到现有PDF
            c = canvas.Canvas(
                str(self.config.output_path),
                pagesize=(page_width, page_height)
            )

            # 从右到左绘制每一列
            for i, (trad_text, simp_text, bbox) in enumerate(
                zip(page.trad_texts, page.simp_texts, page.column_bboxes)
            ):
                x1, y1, x2, y2 = bbox

                # 计算竖排文本的起始位置
                # 注意：这里使用右上角作为起点，从右向左排列
                start_x = x2 - self.config.font_size * 1.5
                start_y = y2 - self.config.font_size * 1.2

                # 绘制简体文本（竖排）
                self.create_vertical_text(
                    c,
                    simp_text,
                    start_x,
                    start_y,
                    font_size=self.config.font_size
                )

            # 结束当前页面
            c.showPage()
            c.save()

            logger.info(f"页面 {page.page_index} 渲染完成")
        except Exception as e:
            logger.error(f"渲染页面失败: {e}")
            raise

    def render_pages(self, pages: List[RenderedPage]) -> Path:
        """
        渲染多个页面到PDF

        Args:
            pages: 要渲染的页面列表

        Returns:
            Path: 生成的PDF文件路径
        """
        # 清除之前的输出文件（如果存在）
        if self.config.output_path.exists():
            self.config.output_path.unlink()

        # 渲染每个页面
        for page in pages:
            self.render_page(page)

        logger.info(f"已生成竖排PDF文件: {self.config.output_path}")
        return self.config.output_path


def create_pdf_composer(config: RenderConfig) -> PdfComposer:
    """
    创建PDF排版器实例

    Args:
        config: 渲染配置

    Returns:
        PdfComposer: 排版器实例
    """
    return PdfComposer(config)


def create_simplified_pdf(
    pages: List[RenderedPage],
    output_path: Path,
    font_path: str,
    font_size: int = 12,
    line_spacing_ratio: float = 1.5
) -> Path:
    """
    根据渲染页面列表创建简体中文竖排PDF

    Args:
        pages: 要渲染的页面列表
        output_path: 输出PDF路径
        font_path: 字体文件路径
        font_size: 字体大小
        line_spacing_ratio: 行间距倍数

    Returns:
        Path: 生成的PDF文件路径
    """
    config = RenderConfig(
        output_path=output_path,
        font_path=font_path,
        font_size=font_size,
        line_spacing_ratio=line_spacing_ratio
    )

    composer = create_pdf_composer(config)
    return composer.render_pages(pages)
