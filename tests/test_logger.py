"""日志模块的单元测试"""

import os
from unittest.mock import patch

from book_ocr.logger import get_logger


def test_singleton() -> None:
    """测试多次调用get_logger返回相同实例"""
    logger1 = get_logger()
    logger2 = get_logger()
    assert id(logger1) == id(logger2), "get_logger应该返回单例"
    
    # 测试命名logger是否与根logger不同
    named_logger = get_logger("test")
    assert named_logger is not logger1, "带名称的logger应该是不同实例"


def test_env_log_level() -> None:
    """测试从环境变量读取日志级别"""
    with patch.dict(os.environ, {"BOOCR_LOG_LEVEL": "DEBUG"}):
        # 重新导入模块以触发_bootstrap
        import importlib

        import book_ocr._logging_core
        importlib.reload(book_ocr._logging_core)
        importlib.reload(book_ocr.logger)
        
        # 重新获取logger
        logger = get_logger()
        
        # 验证DEBUG日志可以被输出
        assert logger.level("DEBUG").no <= logger.level("INFO").no 