from typing import Optional
import click
import sys
import logging
from pathlib import Path

from boocr.pipeline import run_pipeline

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

@boocr.command()
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True, dir_okay=False, resolve_path=True), help='输入文件路径 (PDF)')
@click.option('--output', 'output_path', required=True, type=click.Path(dir_okay=False, resolve_path=True), help='输出文件路径 (PDF)')
@click.option('--columns', 'columns', type=int, help='手动指定页面分栏数，覆盖自动检测')
@click.option('--font', 'font_path', type=str, help='指定字体文件路径')
def poc(input_path: str, output_path: str, columns: Optional[int], font_path: Optional[str]):
    """[PoC] 概念验证：处理单本 PDF"""
    try:
        click.echo(f"开始处理: {input_path}")

        # 准备额外参数
        params = {}
        if font_path:
            font_path_obj = Path(font_path)
            if not font_path_obj.exists():
                click.echo(f"错误: 字体文件不存在: {font_path}", err=True)
                sys.exit(1)
            params['font_path'] = str(font_path_obj)

        # 调用处理流水线
        output_file = run_pipeline(
            input_path=input_path,
            output_path=output_path,
            columns=columns,
            params=params
        )

        click.echo(f"DONE! 已生成文件: {output_file}")
        sys.exit(0)  # 返回成功状态码

    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        logger.error(f"处理失败: {e}", exc_info=True)
        sys.exit(1)  # 返回错误状态码


if __name__ == '__main__':
    boocr()
