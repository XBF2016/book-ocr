from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import os

from boocr.dataclasses import InputSource, PageImage, ColumnCrop, OcrResult, RenderedPage, RenderConfig
from boocr.pdf_utils import extract_pages_from_pdf
from boocr.image_proc import preprocess_image
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
    3. OCR on full pages with PaddleOCR det+cls+rec (P3)
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
        dpi_val = params.get('dpi', 400)
        logger.info(f"使用 DPI: {dpi_val}")
        page_images = extract_pages_from_pdf(input_path, dpi=dpi_val)
        logger.info(f"成功提取 {len(page_images)} 页")

        # 处理结果存储
        all_ocr_results = []  # 所有页面的OCR结果
        all_rendered_pages = []  # 所有要渲染的页面

        # 创建OCR引擎
        ocr_engine = create_ocr_engine(
            use_gpu=params.get('use_gpu', False),
            auto_download=params.get('auto_download', True),
            det_model_dir=params.get('det_model_dir'),
            rec_model_dir=params.get('rec_model_dir'),
            cls_model_dir=params.get('cls_model_dir'),
            rec_only=params.get('rec_only', False),
        )

        # 创建繁简转换器
        converter = create_converter(config=params.get('convert_config', 't2s'))

        # 逐页处理
        for page_image in page_images:
            logger.info(f"处理第 {page_image.page_index + 1} 页")

            # P1: 图像预处理
            logger.info("步骤 2: 图像预处理")
            processed_page = preprocess_image(page_image, deskew_angle=params.get('deskew_angle', None))

            # 可选：保存 P1 预处理结果，便于调试
            if params.get("save_intermediate", True):
                pdf_stem = Path(input_path).stem
                output_root = Path(params.get("output_root", "output"))
                p1_dir = output_root / pdf_stem / "P1"
                p1_dir.mkdir(parents=True, exist_ok=True)
                p1_img_path = p1_dir / f"page_{page_image.page_index + 1}.png"
                try:
                    from PIL import Image
                    Image.fromarray(processed_page.image).save(p1_img_path)
                    logger.debug("已保存 P1 结果至 %s", p1_img_path)
                except Exception as save_err:
                    logger.warning("保存 P1 结果失败: %s", save_err)

            # P2 已废弃：直接整页 OCR
            logger.info("步骤 3: OCR 识别 (整页 det+cls+rec)")
            h, w = processed_page.image.shape[:2]
            column_crops = [ColumnCrop(
                page_index=page_image.page_index,
                column_index=0,
                bbox=(0, 0, w, h),
                image=processed_page.image,
            )]

            # 执行 OCR
            logger.info("调用 OCR 引擎 ...")
            ocr_results = ocr_engine.process_columns(column_crops)

            # 调试：记录每列 OCR 结果摘要
            for res in ocr_results:
                logger.info(
                    "OCR 结果 - page=%d col=%d len=%d conf=%.2f preview=%r",
                    res.page_index,
                    res.column_index,
                    len(res.text),
                    res.confidence,
                    res.text[:30] if res.text else ""
                )

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
                column_bboxes=[(0, 0, processed_page.image.shape[1], processed_page.image.shape[0])]
            )
            all_rendered_pages.append(rendered_page)

        # P5: 排版渲染
        logger.info("步骤 4: 繁简转换完毕，步骤 5: 排版渲染")
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
