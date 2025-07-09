from enum import Enum
from typing import Optional

import typer

from book_ocr._logging_core import configure
from book_ocr.logger import get_logger

# 获取根logger
logger = get_logger()

# 定义日志级别枚举
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

app = typer.Typer()

# 添加全局日志级别选项
@app.callback()  # type: ignore[misc]
def callback(
    log_level: Optional[LogLevel] = typer.Option(
        None,
        "--log-level",
        help="设置日志级别",
        case_sensitive=False,
    )
) -> None:
    """古籍OCR工具"""
    # 如果指定了日志级别，配置日志系统
    if log_level:
        configure(level=log_level.value)
        logger.debug(f"日志级别设置为: {log_level.value}")

@app.command()  # type: ignore[misc]
def version() -> None:
    """Print package version."""
    import importlib.metadata as importlib_metadata
    version_str = importlib_metadata.version("book-ocr")
    logger.info(f"book-ocr 版本: {version_str}")
    typer.echo(version_str)

def add_numbers(a: int, b: int) -> int:
    # 示例函数
    c = a + b
    return c

if __name__ == "__main__":
    app()  # pragma: no cover
