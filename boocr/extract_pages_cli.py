import click
from pathlib import Path
from PIL import Image
import logging

from boocr.pdf_utils import extract_pages_from_pdf

logger = logging.getLogger(__name__)


@click.command(name="extract")
@click.option('--input', 'input_path', required=False, type=click.Path(exists=True, dir_okay=False, resolve_path=True), help='输入 PDF 文件路径，省略则自动从 input/ 目录选择待处理 PDF')
@click.option('--out_dir', 'out_dir', required=False, type=click.Path(file_okay=False, resolve_path=True), help='输出目录 (默认 output/<pdf名>/P0)')
@click.option('--dpi', 'dpi', type=int, default=400, show_default=True, help='光栅化 DPI (默认为 400)')
def extract_cmd(input_path: str | None, out_dir: str | None, dpi: int):
    """仅执行 P0：将 PDF 拆页并保存为 PNG。

    输入 PDF 经光栅化后，按页序号保存为 `page_<n>.png`。
    """
    try:
        # --------------------------------------------------------------
        # 处理默认 input
        # --------------------------------------------------------------
        if input_path is None:
            pdf_files = list(Path("input").glob("*.pdf"))
            if not pdf_files:
                click.echo("错误: 在 input/ 目录未找到任何 PDF", err=True)
                raise SystemExit(1)

            # 过滤已存在 output/<stem>/ 目录的 PDF，避免重复处理
            candidates = [p for p in pdf_files if not (Path("output") / p.stem).exists()]
            if not candidates:
                click.echo("错误: input/ 目录下的 PDF 均已处理过（output/ 下存在同名目录），请删除或手动指定 --input", err=True)
                raise SystemExit(1)
            if len(candidates) > 1:
                click.echo("错误: 检测到多个待处理 PDF，请使用 --input 指定", err=True)
                for p in candidates:
                    click.echo(f"  - {p}")
                raise SystemExit(1)
            input_path = str(candidates[0])
            click.echo(f"自动选择输入文件: {input_path}")

        logger.info("开始拆页 (P0): %s", input_path)
        pages = extract_pages_from_pdf(input_path, dpi=dpi)

        if out_dir is None:
            pdf_stem = Path(input_path).stem
            out_dir_path = Path("output") / pdf_stem / "P0"
        else:
            out_dir_path = Path(out_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)

        for page in pages:
            img_path = out_dir_path / f"page_{page.page_index + 1}.png"
            Image.fromarray(page.image).save(img_path)
            logger.debug("已保存 %s", img_path)

        click.echo(f"DONE! 已保存 {len(pages)} 页 PNG 至 {out_dir_path}")
    except Exception as e:
        logger.error("拆页失败: %s", e, exc_info=True)
        click.echo(f"错误: {e}", err=True)
        raise SystemExit(1)
