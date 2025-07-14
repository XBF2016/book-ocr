"""
pytest 配置文件

包含测试项目的公共夹具和配置
"""
import os
import sys
import pytest

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 示例夹具
@pytest.fixture
def sample_fixture():
    """示例测试夹具，返回一个简单值"""
    return "测试值"

# 可以在此添加更多的夹具和钩子函数
