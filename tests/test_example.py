"""
示例测试文件

包含基础测试用例，作为项目测试的占位和参考
"""
import pytest


def test_sample():
    """最简单的断言测试示例"""
    assert True


def test_with_fixture(sample_fixture):
    """使用测试夹具的示例"""
    assert isinstance(sample_fixture, str)
    assert len(sample_fixture) > 0


@pytest.mark.parametrize("test_input,expected", [
    (1, 1),
    (2, 2),
    ("a", "a"),
])
def test_parametrized(test_input, expected):
    """参数化测试示例"""
    assert test_input == expected


@pytest.mark.skip(reason="这是一个被跳过的测试示例")
def test_skipped():
    """被跳过的测试示例"""
    assert False  # 永远不会执行
