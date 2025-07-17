import click
import json
import logging
from pathlib import Path
from typing import List, Dict

import numpy as np
from PIL import Image

from boocr.pdf_utils import extract_pages_from_pdf
from boocr.image_proc import preprocess_image, to_grayscale
from boocr.ocr import create_ocr_engine
from boocr.dataclasses import ColumnCrop, OcrResult

logger = logging.getLogger(__name__)

# 动态调整日志级别：将在点击回调中根据 --debug 参数设置


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

def _ensure_dir(path: Path):
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def _load_page_images(p1_dir: Path) -> Dict[int, np.ndarray]:
    """加载 P1 目录中二值化页面 PNG 为 numpy 数组。

    Returns:
        dict: {page_index: image_array}
    """
    pages = {}
    png_files = sorted(p1_dir.glob("page_*.png"))
    if not png_files:
        raise FileNotFoundError(f"在 {p1_dir} 未找到 page_*.png")

    for png_path in png_files:
        # 提取页序号（page_1.png → 0-based 0）
        try:
            page_no = int(png_path.stem.split("_")[1]) - 1
        except Exception:
            continue  # 跳过无法解析的文件名
        img = Image.open(png_path)
        img_gray = img.convert("L")
        pages[page_no] = np.array(img_gray)
    return pages


def _build_full_page_crops(pdf_path: Path, dpi: int = 400) -> List[ColumnCrop]:
    """从输入 PDF 构造整页 ColumnCrop 列表（单列，包含整张页面）。"""
    from boocr.pdf_utils import extract_pages_from_pdf
    from boocr.image_proc import preprocess_image
    logger.info("开始从 PDF 构建整页 ColumnCrop ...")

    page_images = extract_pages_from_pdf(pdf_path, dpi=dpi)
    logger.info("成功提取 %d 页", len(page_images))

    column_crops: List[ColumnCrop] = []
    for page in page_images:
        processed_page = preprocess_image(page)
        h, w = processed_page.image.shape[:2]
        column_crops.append(ColumnCrop(
            page_index=page.page_index,
            column_index=0,
            bbox=(0, 0, w, h),
            image=processed_page.image,
        ))
    return column_crops


def _build_column_crops(p2_dir: Path) -> List[ColumnCrop]:
    """根据 P2 目录中的 columns.json 或列 PNG 构造 ColumnCrop 列表。"""
    json_path = p2_dir / "columns.json"
    if json_path.exists():
        # ---------------- 从 columns.json 构建 ---------------------
        with open(json_path, "r", encoding="utf-8") as f:
            cols_data = json.load(f)

        # 尝试加载 P1 图像供裁剪（若直接保存了列 PNG 也可优先使用）
        p1_dir = p2_dir.parent / "P1"
        page_images = {}
        if p1_dir.exists():
            try:
                page_images = _load_page_images(p1_dir)
            except Exception as e:
                logger.warning("加载 P1 图像失败: %s", e)

        column_crops: List[ColumnCrop] = []
        for page_info in cols_data:
            page_idx = int(page_info.get("page_index", 0))
            bboxes = page_info.get("bboxes", [])
            for col_idx, bbox in enumerate(bboxes):
                x1, y1, x2, y2 = [int(v) for v in bbox]
                crop_img_path = p2_dir / f"page_{page_idx + 1}_col_{col_idx + 1}.png"
                if crop_img_path.exists():
                    try:
                        img = Image.open(crop_img_path).convert("L")
                        img_arr = np.array(img)
                    except Exception as e:
                        logger.warning("读取列裁剪 PNG 失败: %s", e)
                        img_arr = None
                else:
                    img_arr = None

                # 若未能直接加载列 PNG，则退回到 P1 图像裁剪
                if img_arr is None:
                    if page_idx not in page_images:
                        logger.warning("缺少 page_%d.png，且列 PNG 不存在，跳过该列", page_idx + 1)
                        continue
                    page_img = page_images[page_idx]
                    img_arr = page_img[y1:y2, x1:x2]

                column_crops.append(ColumnCrop(
                    page_index=page_idx,
                    column_index=col_idx,
                    bbox=(x1, y1, x2, y2),
                    image=img_arr,
                ))
        return column_crops

    # ---------------- Fallback: 从列 PNG 构建 --------------------
    logger.info("columns.json 不存在，尝试从列 PNG 构建 ColumnCrop ...")
    import re
    pattern = re.compile(r"page_(\d+)_col_(\d+)\.png$")
    column_crops: List[ColumnCrop] = []
    for png_path in sorted(p2_dir.glob("page_*_col_*.png")):
        m = pattern.match(png_path.name)
        if not m:
            continue
        page_idx = int(m.group(1)) - 1
        col_idx = int(m.group(2)) - 1
        try:
            img = Image.open(png_path).convert("L")
            img_arr = np.array(img)
        except Exception as e:
            logger.warning("读取 %s 失败: %s", png_path, e)
            continue
        h, w = img_arr.shape[:2]
        column_crops.append(ColumnCrop(
            page_index=page_idx,
            column_index=col_idx,
            bbox=(0, 0, w, h),
            image=img_arr,
        ))

    if not column_crops:
        raise FileNotFoundError(f"在 {p2_dir} 未发现列 PNG (page_*_col_*.png) 或 columns.json")

    return column_crops


def _ensure_p2_from_pdf(pdf_path: Path, dpi: int = 400) -> Path:
    """若不存在 P2 目录则执行 P0+P1+P2 并返回 P2 目录路径。"""
    pdf_stem = pdf_path.stem
    output_root = Path("output") / pdf_stem
    p1_dir = output_root / "P1"
    p2_dir = output_root / "P2"

    if p2_dir.exists() and (p2_dir / "columns.json").exists():
        return p2_dir

    logger.info("未找到 P2 结果，开始执行 P0 + P1 + P2")

    # P0: 拆页
    pages = extract_pages_from_pdf(pdf_path, dpi=dpi)

    # P1: 预处理
    _ensure_dir(p1_dir)
    processed_pages = []
    for page in pages:
        proc_page = preprocess_image(page)
        processed_pages.append(proc_page)
        img_path = p1_dir / f"page_{proc_page.page_index + 1}.png"
        Image.fromarray(proc_page.image).save(img_path)

    # P2: 列检测
    _ensure_dir(p2_dir)
    results_json = []
    for proc_page in processed_pages:
        bboxes = detect_columns(proc_page.image)
        results_json.append({
            "page_index": int(proc_page.page_index),
            "bboxes": [[int(v) for v in b] for b in bboxes],
        })
    # 保存 JSON
    with open(p2_dir / "columns.json", "w", encoding="utf-8") as f:
        json.dump(results_json, f, ensure_ascii=False, indent=2)

    logger.info("P0+P1+P2 完成，共处理 %d 页", len(processed_pages))
    return p2_dir


# ---------------------------------------------------------------------------
# Click CLI 定义
# ---------------------------------------------------------------------------

@click.command(name="ocr")
@click.option('--debug/--no-debug', default=False, help='启用 DEBUG 日志')
@click.option('--input', 'input_path', required=False,
              type=click.Path(exists=True, resolve_path=True),
              help='输入：P2 目录 或 PDF 文件。若省略则自动发现唯一 P2 目录')
# 新增：直接输入单张页面 PNG（P0 导出）
@click.option('--image', 'image_path', required=False,
              type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              help='输入：单张页面 PNG (P0 输出)，与 --input 互斥')
@click.option('--out_dir', 'out_dir', required=False,
              type=click.Path(file_okay=False, resolve_path=True),
              help='输出目录 (默认 output/<PDF名>/P3)')
@click.option('--use_gpu/--no-use_gpu', default=False, help='是否使用GPU推理')
@click.option('--batch_size', 'batch_size', type=int, required=False, help='批大小 (预留)')
@click.option('--save_text_blocks/--no-save_text_blocks', 'save_blocks', default=False, help='是否保存单列文本 txt')
@click.option('--dpi', 'dpi', type=int, default=400, show_default=True, help='光栅化 PDF 时使用的 DPI')
@click.option('--skip_model_check', is_flag=True, default=False, help='跳过自定义模型下载/校验 (直接由 PaddleOCR 处理)')
@click.option('--det_model_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), default=None, help='自定义 det 模型目录')
@click.option('--rec_model_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), default=None, help='自定义 rec 模型目录')
@click.option('--cls_model_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), default=None, help='自定义 cls 模型目录')
@click.option('--rec_only', is_flag=True, default=False, help='仅使用 rec-only 纯识别（跳过 det/cls），用于超长竖排兜底')
def ocr_cmd(
    debug: bool,
    input_path: str | None,
    image_path: str | None,  # 新增：单张图片路径
    out_dir: str | None,
    use_gpu: bool,
    batch_size: int | None,
    save_blocks: bool,
    dpi: int,
    skip_model_check: bool,
    det_model_dir: str | None,
    rec_model_dir: str | None,
    cls_model_dir: str | None,
    rec_only: bool,

):
    """仅执行 P3：对已切列图像进行 OCR，并输出 JSON/TXT 结果。"""

    # ------------------------------------------------------------------
    # Configure logging level according to --debug flag so that
    # _save_debug_patch() inside boocr.ocr can work.
    # ------------------------------------------------------------------
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                            format="[%(asctime)s] [%(levelname)s] %(message)s")
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO,
                            format="[%(asctime)s] [%(levelname)s] %(message)s")
    try:
        # ------------------------------------------------------------------
        # 1. 解析输入，构建 ColumnCrop
        #    支持三种输入：PDF（原模式）、P2 目录（原）、单张 PNG（新增）
        # ------------------------------------------------------------------
        # --image 与 --input 互斥
        if image_path and input_path:
            raise click.ClickException("--image 与 --input 互斥，请二选一")

        # ------------------------- 单张 PNG 路径 -------------------------
        if image_path:
            img_path = Path(image_path)
            if not img_path.is_file():
                raise click.ClickException("--image 必须为 PNG 文件路径")

            from PIL import Image  # 局部导入，避免无用依赖
            import numpy as np

            img = Image.open(img_path).convert("L")
            img_arr = np.array(img)
            h, w = img_arr.shape[:2]

            # -------------- 预处理（仅 deskew，不二值化） --------------
            # 保持灰度图，避免强烈二值化导致检测失败。
            # 使用轻量预处理：仅自动倾斜校正（deskew），保持灰度图，避免过度二值化导致 det 失败
            from boocr.image_proc import deskew
            # deskew 会自动检测角度
            proc_img, _angle = deskew(img_arr)
            import cv2  # 本段后续将用到 cv2，提前导入

            h_proc, w_proc = proc_img.shape[:2]

            column_crops: List[ColumnCrop] = [ColumnCrop(
                page_index=0,
                column_index=0,
                bbox=(0, 0, w_proc, h_proc),
                image=proc_img,
            )]

            # 用文件名作为 stem
            pdf_stem = img_path.stem

        # ------------------------- 原有 PDF 路径 -------------------------
        else:
            if input_path is None:
                raise click.ClickException("请使用 --input 指定 PDF 文件路径，或使用 --image 指定 PNG")

            pdf_path = Path(input_path)
            if not pdf_path.is_file():
                raise click.ClickException("--input 必须为 PDF 文件路径")

            pdf_stem = pdf_path.stem
            # 仍然按整页构建 ColumnCrop
            column_crops = _build_full_page_crops(pdf_path, dpi=dpi)
        logger.info("共加载 %d 个页面", len(column_crops))

        # ------------------------------------------------------------------
        # 2. 已在前面构建整页 ColumnCrop
        # ------------------------------------------------------------------

        # ------------------------------------------------------------------
        # 3. 初始化 OCR 引擎
        # ------------------------------------------------------------------
        ocr_engine = create_ocr_engine(
            use_gpu=use_gpu,
            auto_download=not skip_model_check,
            det_model_dir=det_model_dir,
            rec_model_dir=rec_model_dir,
            cls_model_dir=cls_model_dir,
            rec_only=rec_only,
        )

        # ------------------------------------------------------------------
        # 4. 执行 OCR
        # ------------------------------------------------------------------
        # 目前 batch_size 参数保留
        ocr_results: List[OcrResult] = ocr_engine.process_columns(column_crops)

        # 若全部列均未识别出文本，则视为整体失败（可能模型缺失或初始化问题）
        if not any(r.text.strip() for r in ocr_results):
            raise click.ClickException("OCR 识别失败：所有列均未检测到文本，可能是模型未正确加载。")

        # ------------------------------------------------------------------
        # 5. 输出结果目录
        # ------------------------------------------------------------------
        if out_dir is None:
            out_dir_path = Path("output") / pdf_stem / "P3"
        else:
            out_dir_path = Path(out_dir)
        _ensure_dir(out_dir_path)

        # JSON
        json_path = out_dir_path / "ocr_results.json"
        json_data = [
            {
                "page_index": r.page_index,
                "column_index": r.column_index,
                "text": r.text,
                "confidence": r.confidence,
            }
            for r in ocr_results
        ]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # TXT（按页拼接）
        txt_path = out_dir_path / "ocr_results.txt"
        page_dict: Dict[int, List[OcrResult]] = {}
        for res in ocr_results:
            page_dict.setdefault(res.page_index, []).append(res)
        with open(txt_path, "w", encoding="utf-8") as f:
            for page_idx in sorted(page_dict.keys()):
                # 按列序号排序
                page_results = sorted(page_dict[page_idx], key=lambda r: r.column_index)
                for res in page_results:
                    f.write(res.text or "")
                    f.write("\n")
                # 页面间空行分隔
                f.write("\n")

        # 单列文本块
        if save_blocks:
            for res in ocr_results:
                block_path = out_dir_path / f"page_{res.page_index + 1}_col_{res.column_index + 1}.txt"
                with open(block_path, "w", encoding="utf-8") as bf:
                    bf.write(res.text or "")

        click.echo(f"DONE! OCR 已完成，结果已保存至 {out_dir_path}")
        raise SystemExit(0)

    except click.ClickException as ce:
        # 已处理的用户输入错误
        raise ce  # 让 Click 处理输出
    except Exception as e:
        logger.error("OCR 处理失败: %s", e, exc_info=True)
        click.echo(f"错误: {e}", err=True)
        raise SystemExit(1)
