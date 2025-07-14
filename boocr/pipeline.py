from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import os

from boocr.dataclasses import InputSource, PageImage, ColumnCrop, OcrResult, RenderedPage, RenderConfig
from boocr.pdf_utils import extract_pages_from_pdf
from boocr.image_proc import preprocess_image
from boocr.col_detect import detect_columns
from boocr.ocr import create_ocr_engine
from boocr.converter import create_converter
from boocr.composer import create_pdf_composer

# 配置日志
logger = logging.getLogger(__name__)

def run_pipeline(
    input_path: str,
    output_path: str,
    columns: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
):
    """
    The main processing pipeline for OCR.

    This function will orchestrate the following steps:
    1. PDF parsing and image conversion (P0)
    2. Image preprocessing (P1)
    3. Column detection and cropping (P2)
    4. OCR on cropped columns (P3)
    5. Text conversion (Simplified Chinese) (P4)
    6. Rendering the final output PDF (P5)

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path to save the output file.
        columns (Optional[int], optional): Number of columns to override auto-detection. Defaults to None.
        params (Dict[str, Any], optional): Additional parameters to control the pipeline. Defaults to None.
    """
    logger.info(f"启动OCR处理流水线...")
    logger.info(f"输入文件: {input_path}")
    logger.info(f"输出文件: {output_path}")

    if columns:
        logger.info(f"列数覆盖设置: {columns}")
    if params is None:
        params = {}

    try:
        # 确保输出路径的目录存在
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # 默认字体路径，可通过params覆盖
        default_font_path = params.get('font_path', "simsun.ttc")  # 默认使用系统字体
        font_size = params.get('font_size', 12)
        line_spacing = params.get('line_spacing', 1.5)

        # P0: PDF解析和图像转换
        logger.info("步骤 1: PDF解析和图像转换")
        page_images = extract_pages_from_pdf(input_path)
        logger.info(f"成功提取 {len(page_images)} 页")

        # 处理结果存储
        all_ocr_results = []  # 所有页面的OCR结果
        all_rendered_pages = []  # 所有要渲染的页面

        # 创建OCR引擎
        ocr_engine = create_ocr_engine(use_gpu=params.get('use_gpu', False))

        # 创建繁简转换器
        converter = create_converter(config=params.get('convert_config', 't2s'))

        # 逐页处理
        for page_image in page_images:
            logger.info(f"处理第 {page_image.page_index + 1} 页")

            # P1: 图像预处理
            logger.info("步骤 2: 图像预处理")
            processed_page = preprocess_image(page_image, deskew_angle=params.get('deskew_angle', None))

            # P2: 列检测与裁切
            logger.info("步骤 3: 列检测与裁切")
            column_bboxes = detect_columns(processed_page.image, num_columns=columns)
            logger.info(f"检测到 {len(column_bboxes)} 列")

            # 创建ColumnCrop对象列表
            column_crops = []
            for col_idx, bbox in enumerate(column_bboxes):
                x1, y1, x2, y2 = bbox
                # 裁切列图像
                col_image = processed_page.image[y1:y2, x1:x2]

                column_crop = ColumnCrop(
                    page_index=page_image.page_index,
                    column_index=col_idx,
                    bbox=bbox,
                    image=col_image
                )
                column_crops.append(column_crop)

            # P3: OCR识别
            logger.info("步骤 4: OCR识别")
            ocr_results = ocr_engine.process_columns(column_crops)
            all_ocr_results.extend(ocr_results)

            # P4: 繁简转换
            logger.info("步骤 5: 繁简转换")
            trad_and_simp_texts = converter.process_ocr_results(ocr_results)

            # 准备渲染数据
            trad_texts = [pair[0] for pair in trad_and_simp_texts]
            simp_texts = [pair[1] for pair in trad_and_simp_texts]

            # 创建RenderedPage对象
            rendered_page = RenderedPage(
                page_index=page_image.page_index,
                page_size=(page_image.width, page_image.height),
                trad_texts=trad_texts,
                simp_texts=simp_texts,
                column_bboxes=column_bboxes
            )
            all_rendered_pages.append(rendered_page)

        # P5: 排版渲染
        logger.info("步骤 6: 排版渲染")
        render_config = RenderConfig(
            output_path=Path(output_path),
            font_path=default_font_path,
            font_size=font_size,
            line_spacing_ratio=line_spacing
        )

        pdf_composer = create_pdf_composer(render_config)
        output_file = pdf_composer.render_pages(all_rendered_pages)

        logger.info(f"处理完成，已生成输出文件: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"处理流水线失败: {e}", exc_info=True)
        raise RuntimeError(f"OCR流水线执行失败: {str(e)}")
