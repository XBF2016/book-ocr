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
        # 尝试按顺序注册字体，确保PDF中包含可搜索的中文字符
        font_candidates = []

        # 1) 用户配置的字体
        if self.config.font_path:
            font_candidates.append(("ChineseFont", self.config.font_path))

        # 2) 常见系统字体（Windows SimSun）
        win_simsun = Path(r"C:\Windows\Fonts\simsun.ttc")
        if win_simsun.exists():
            font_candidates.append(("SimSun", str(win_simsun)))

        # 依次尝试 TrueType 字体
        for fname, fpath in font_candidates:
            try:
                pdfmetrics.registerFont(TTFont(fname, fpath))
                self.font_name = fname
                logger.info(f"成功注册字体: {fpath}")
                return
            except Exception as e:
                logger.warning(f"无法注册字体 {fpath}: {e}")

        # 3) 尝试使用内置 CID 字体（不依赖外部文件）
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            cid_font_name = "STSong-Light"
            pdfmetrics.registerFont(UnicodeCIDFont(cid_font_name))
            self.font_name = cid_font_name
            logger.info(f"使用内置 CID 字体: {cid_font_name}")
            return
        except Exception as e:
            logger.error(f"内置 CID 字体注册失败: {e}")

        # 4) 最后回退到 Helvetica（可能不支持中文，文本可能不可见）
        self.font_name = "Helvetica"
        logger.error("未能成功注册任何中文字体，已回退至 Helvetica，可能导致文本不可见或不可搜索。")

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
        在Canvas上创建竖排文本，确保文本可搜索

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

            # 逐字绘制，每个字符确保可搜索
            for char in line:
                # 添加文字并确保文字可搜索
                # 使用正确的Unicode编码绘制文本
                canvas_obj.drawString(current_x, current_y, char)

                # 移动到下一个字符位置
                current_y -= font_size  # 向下移动一个字符高度

            # 下一列
            current_x += char_height
            current_y = y  # 重置y坐标到顶部

        canvas_obj.restoreState()

    def render_pages(self, pages: List[RenderedPage]) -> Path:
        """
        渲染多个页面到PDF

        Args:
            pages: 要渲染的页面列表

        Returns:
            Path: 生成的PDF文件路径
        """

        # 采用临时文件写入，避免被占用时直接unlink报错
        import tempfile, shutil
        output_path = self.config.output_path
        temp_output_path = output_path.with_suffix('.tmp' + output_path.suffix)
        if temp_output_path.exists():
            temp_output_path.unlink()

        # 如果输出文件夹不存在，则创建
        output_dir = self.config.output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # 使用单一 Canvas 生成多页 PDF，避免后续合并导致的内容丢失
        # 先创建临时输出 Canvas
        first_page_size = pages[0].page_size
        c = canvas.Canvas(str(temp_output_path), pagesize=first_page_size)

        for i, page in enumerate(pages):
            # 如果当前页面尺寸与上一个不同，更新 pagesize
            if i != 0:
                c.setPageSize(page.page_size)

            # 设置文档属性以增强可搜索性
            c.setTitle(f"古籍竖排繁简对照 - 第{page.page_index+1}页")
            c.setSubject("古籍竖排繁简对照")
            c.setAuthor("BOOCR")
            c.setCreator("BOOCR古籍处理工具")
            c.setKeywords("古籍 竖排 繁简对照 可搜索")

            # TODO: 研究如何正确设置PDF文档的 /Lang 属性
            # c.setViewerPreference('Language', 'zh-CN')

            # 使用压缩以减小文件大小
            c.setPageCompression(1)

            # 从右到左绘制每一列
            for j, (trad_text, simp_text, bbox) in enumerate(
                zip(page.trad_texts, page.simp_texts, page.column_bboxes)
            ):
                x1, y1, x2, y2 = bbox

                # ReportLab 坐标系以页面左下角为原点，而图像/像素坐标通常以左上角为原点。
                # 需要将像素 y 坐标翻转为 PDF 坐标。
                page_height = page.page_size[1]

                # 转换后的 bbox 顶部 y 坐标
                pdf_y_top = page_height - y1

                # 计算竖排文本的起始位置：
                #   - X 轴：列右边缘往左偏移一个字符宽度，保持与图像中列对齐
                #   - Y 轴：从列顶部开始向下绘制
                start_x = x2 - self.config.font_size * 1.5
                start_y = pdf_y_top - self.config.font_size * 1.2

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

            logger.info(f"页面 {page.page_index} 渲染完成")

        # 保存 PDF
        c.save()

        # 不再需要跨页合并逻辑
        logger.info(f"已生成 {len(pages)} 页 PDF 文件")

        # 原子替换到目标路径
        try:
            if output_path.exists():
                output_path.unlink()
            shutil.move(str(temp_output_path), str(output_path))
        except Exception as e:
            logger.error(f"PDF写入目标路径失败: {e}")
            raise

        logger.info(f"已生成竖排PDF文件: {output_path}")
        return output_path


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
    pdf_path = composer.render_pages(pages)

    # 确保PDF是可搜索的，添加文档级别的元数据
    # 注：ReportLab已经在每页渲染时添加了元数据和可搜索性

    logger.info(f"已生成可搜索的竖排PDF文件: {pdf_path}")
    return pdf_path
