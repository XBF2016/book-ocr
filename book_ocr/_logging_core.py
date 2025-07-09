import logging
import os
import sys
from typing import Any

from loguru import logger


def _bootstrap() -> None:
    """初始化日志系统的默认配置，在模块首次导入时调用"""
    # 从环境变量获取日志级别，默认为INFO
    log_level = os.environ.get("BOOCR_LOG_LEVEL", "INFO").upper()
    
    # 移除默认的sink
    logger.remove()
    
    # 添加stderr彩色输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[module]}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # 拦截标准logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0)


def configure(**kwargs: Any) -> None:
    """配置日志系统，CLI启动时调用以覆盖默认配置
    
    Args:
        **kwargs: 支持的参数包括：
            - level: 日志级别，如"DEBUG", "INFO"等
            - 其他loguru.add()支持的参数
    """
    # 如果指定了level，先移除默认sink再添加新sink
    if kwargs:
        logger.remove()
        logger.add(sys.stderr, colorize=True, **kwargs)


class InterceptHandler(logging.Handler):
    """将标准logging的日志重定向到loguru"""
    def emit(self, record: logging.LogRecord) -> None:
        # 尝试将标准logging的级别映射到loguru的级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        # 将模块名绑定到日志中
        logger.bind(module=record.name).log(level, record.getMessage()) 