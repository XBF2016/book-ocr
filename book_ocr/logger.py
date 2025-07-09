"""
日志模块，提供统一的日志接口

使用方法:
    from book_ocr.logger import get_logger
    
    # 默认logger
    logger = get_logger()
    logger.info("这是一条普通日志")
    
    # 带模块名的logger
    module_logger = get_logger("module_name")
    module_logger.debug("这是模块的调试日志")
"""

from typing import Optional

from loguru import logger as _root_logger

from ._logging_core import _bootstrap

# 首次导入时完成默认配置
_bootstrap()


def get_logger(name: Optional[str] = None) -> _root_logger.__class__:
    """
    获取日志记录器
    
    Args:
        name: 模块名称，为None时返回根logger
        
    Returns:
        配置好的logger实例
    """
    if name is None:
        return _root_logger
    return _root_logger.bind(module=name) 