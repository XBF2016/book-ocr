import click
import logging
from pathlib import Path
from PIL import Image
import numpy as np

from boocr.pdf_utils import extract_pages_from_pdf
from boocr.image_proc import preprocess_image

from boocr.dataclasses import PageImage  # 延迟 import 避免循环


logger = logging.getLogger(__name__)


def _load_pages_from_png_dir(p0_dir: Path) -> list["PageImage"]:
    """从 P0 目录加载 page_*.png 并返回 PageImage 列表。"""

    png_files = sorted(p0_dir.glob("page_*.png"))
    if not png_files:
        raise FileNotFoundError(f"在 {p0_dir} 未找到 page_*.png")

    pages: list[PageImage] = []
    for idx, png_path in enumerate(png_files):
        img = Image.open(png_path)
        img_rgb = img.convert("RGB")  # 保证一致
        img_array = np.array(img_rgb)
        pages.append(PageImage(
            page_index=idx,
            image=img_array,
            width=img_array.shape[1],
            height=img_array.shape[0],
        ))
    return pages


@click.command(name="preproc")
@click.option('--input', 'input_path', required=False, type=click.Path(exists=True, resolve_path=True), help='输入路径：可为 PDF 文件或 P0 目录；若省略则自动发现唯一 P0 目录')
@click.option('--out_dir', 'out_dir', required=False, type=click.Path(file_okay=False, resolve_path=True), help='输出目录 (默认 output/<PDF名>/P1)')
@click.option('--dpi', 'dpi', type=int, default=400, show_default=True, help='光栅化 DPI (PDF 模式下生效)')
@click.option('--deskew_angle', 'deskew_angle', type=float, required=False, help='手动指定倾斜校正角度 (度)。若省略则自动检测')
def preproc_cmd(input_path: str | None, out_dir: str | None, dpi: int, deskew_angle: float | None):
    """仅执行 P1：对 PDF 页面进行预处理并保存二值化结果。

    处理流程：拆页 → 预处理 → 保存 PNG。
    """
    try:
        if input_path is None:
            # 自动扫描 output/*/P0 目录
            candidates = list(Path("output").glob("*/P0"))
            candidates = [p for p in candidates if any(p.glob("page_*.png"))]
            if not candidates:
                raise click.ClickException("未找到任何 P0 目录，请先执行 boocr extract 或手动指定 --input")
            if len(candidates) > 1:
                msg = "检测到多个 P0 目录，请用 --input 指定其中文件或目录:\n" + "\n".join(str(c) for c in candidates)
                raise click.ClickException(msg)
            in_path = candidates[0]
            logger.info("自动选择 P0 目录: %s", in_path)
        else:
            in_path = Path(input_path)

        logger.info("开始预处理 (P1): %s", in_path)

        # 根据输入类型选择加载方式
        if in_path.is_dir():
            # 目录 ⇒ 读取 page_*.png
            pages = _load_pages_from_png_dir(in_path)
            pdf_stem = in_path.parent.name  # 上级目录名即 PDF 名 (output/<pdf_stem>/P0)
        else:
            # PDF 文件 ⇒ 优先尝试复用 P0 目录
            pdf_stem = in_path.stem
            p0_dir = Path("output") / pdf_stem / "P0"
            if p0_dir.exists() and any(p0_dir.glob("page_*.png")):
                logger.info("检测到 P0 目录，直接复用拆页 PNG: %s", p0_dir)
                pages = _load_pages_from_png_dir(p0_dir)
            else:
                logger.info("未找到 P0 目录或为空，重新光栅化 PDF")
                pages = extract_pages_from_pdf(in_path, dpi=dpi)

        # 确定输出目录
        if out_dir is None:
            out_dir_path = Path("output") / pdf_stem / "P1"
        else:
            out_dir_path = Path(out_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)

        processed_count = 0
        for page in pages:
            processed_page = preprocess_image(page, deskew_angle=deskew_angle)
            img_path = out_dir_path / f"page_{processed_page.page_index + 1}.png"
            # 处理后的图像是二值化结果，使用 "L" 模式保存可减小文件大小
            Image.fromarray(processed_page.image).save(img_path)
            logger.debug("已保存 %s", img_path)
            processed_count += 1

        click.echo(f"DONE! 已保存 {processed_count} 页 PNG 至 {out_dir_path}")
    except Exception as e:
        logger.error("预处理失败: %s", e, exc_info=True)
        click.echo(f"错误: {e}", err=True)
        raise SystemExit(1)
