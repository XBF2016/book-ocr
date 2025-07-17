from typing import Optional
import click
import sys
import logging
from pathlib import Path

# 注意：避免在导入 CLI 时立刻加载 heavy 依赖（如 Paddle）。
# 仅在执行 `poc` 子命令时再动态导入 run_pipeline。
from boocr.extract_pages_cli import extract_cmd as extract_cmd
from boocr.preprocess_cli import preproc_cmd as preproc_cmd
from boocr.ocr_cli import ocr_cmd as ocr_cmd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@click.group()
def boocr():
    """古籍影印本竖排繁简转换工具"""
    pass

# 注册子命令：仅执行 P0 拆页导出
boocr.add_command(extract_cmd)
boocr.add_command(preproc_cmd)
boocr.add_command(ocr_cmd)

@boocr.command()
@click.option('--input', 'input_path', required=False, type=click.Path(dir_okay=False, resolve_path=True), help='输入文件路径 (PDF)，默认读取 input/ 目录下唯一的 PDF')
@click.option('--output', 'output_path', required=False, type=click.Path(dir_okay=False, resolve_path=True), help='输出文件路径 (PDF)，默认写入 output/<PDF名>/<PDF名>_out.pdf')
@click.option('--columns', 'columns', type=int, help='手动指定页面分栏数，覆盖自动检测')
@click.option('--font', 'font_path', type=str, help='指定字体文件路径')
@click.option('--det_model_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), help='自定义 det 模型目录')
@click.option('--rec_model_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), help='自定义 rec 模型目录')
@click.option('--cls_model_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True), help='自定义 cls 模型目录')
@click.option('--rec_only', is_flag=True, default=False, help='仅使用 rec-only 纯识别')
@click.option('--dpi', 'dpi', type=int, default=400, show_default=True, help='光栅化 DPI（上限，默认为 400，可提高清晰度）')
def poc(input_path: str | None, output_path: str | None, columns: Optional[int], font_path: Optional[str], det_model_dir: str | None, rec_model_dir: str | None, cls_model_dir: str | None, rec_only: bool, dpi: int):
    """[PoC] 概念验证：处理单本 PDF"""
    try:
        # --------------------------------------------------------------
        # 处理默认 input/output
        # --------------------------------------------------------------
        if input_path is None:
            pdf_files = list(Path("input").glob("*.pdf"))
            if not pdf_files:
                click.echo("错误: 在 input/ 目录未找到任何 PDF", err=True)
                sys.exit(1)
            if len(pdf_files) > 1:
                click.echo("错误: input/ 目录下存在多个 PDF，请使用 --input 指定", err=True)
                for p in pdf_files:
                    click.echo(f"  - {p}")
                sys.exit(1)
            input_path = str(pdf_files[0])
            click.echo(f"自动选择输入文件: {input_path}")
        else:
            input_path = str(Path(input_path))

        if output_path is None:
            stem = Path(input_path).stem
            out_dir = Path("output") / stem
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(out_dir / f"{stem}_out.pdf")
            click.echo(f"自动设置输出文件: {output_path}")

        click.echo(f"开始处理: {input_path}")

        # 准备额外参数
        params = {}
        if font_path:
            font_path_obj = Path(font_path)
            if not font_path_obj.exists():
                click.echo(f"错误: 字体文件不存在: {font_path}", err=True)
                sys.exit(1)
            params['font_path'] = str(font_path_obj)

        # 将用户参数写入 params
        params['dpi'] = dpi
        # 如果用户未显式提供模型路径，但项目自带模型目录存在，则自动填充
        proj_model_root = Path(__file__).parent / "ocr_model"
        if det_model_dir is None:
            default_det = proj_model_root / "PP-OCRv5_server_det_infer"
            if default_det.exists():
                det_model_dir = str(default_det)
        if rec_model_dir is None:
            default_rec = proj_model_root / "chinese_cht_PP-OCRv3_mobile_rec_infer"
            if default_rec.exists():
                rec_model_dir = str(default_rec)
        if cls_model_dir is None:
            default_cls = proj_model_root / "ch_ppocr_mobile_v2.0_cls_infer"  # 可能的目录名
            if default_cls.exists():
                cls_model_dir = str(default_cls)

        # 写入 params
        params['det_model_dir'] = det_model_dir
        params['rec_model_dir'] = rec_model_dir
        params['cls_model_dir'] = cls_model_dir
        params['rec_only'] = rec_only

        # 如果提供了任意模型目录，则关闭自动下载
        params['auto_download'] = not (det_model_dir or rec_model_dir or cls_model_dir)

        # 延迟导入，避免未使用 `poc` 时加载繁重依赖
        from boocr.pipeline import run_pipeline

        # 调用处理流水线
        output_file = run_pipeline(
            input_path=input_path,
            output_path=output_path,
            columns=columns,
            params=params,
        )

        click.echo(f"DONE! 已生成文件: {output_file}")
        sys.exit(0)  # 返回成功状态码

    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        logger.error(f"处理失败: {e}", exc_info=True)
        sys.exit(1)  # 返回错误状态码


if __name__ == '__main__':
    boocr()
