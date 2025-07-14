from typing import Optional
import click

@click.group()
def boocr():
    """古籍影印本竖排繁简转换工具"""
    pass

@boocr.command()
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True, dir_okay=False, resolve_path=True), help='输入文件路径 (PDF)')
@click.option('--output', 'output_path', required=True, type=click.Path(dir_okay=False, resolve_path=True), help='输出文件路径 (PDF)')
@click.option('--columns', 'columns', type=int, help='手动指定页面分栏数，覆盖自动检测')
def poc(input_path: str, output_path: str, columns: Optional[int]):
    """[PoC] 概念验证：处理单本 PDF"""
    click.echo("TODO: Implement the pipeline")
    click.echo(f"Input file: {input_path}")
    click.echo(f"Output file: {output_path}")
    if columns:
        click.echo(f"Columns override: {columns}")


if __name__ == '__main__':
    boocr()
