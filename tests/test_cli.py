from book_ocr.cli import add_numbers


def test_addition_function() -> None:
    """测试示例函数."""
    assert add_numbers(1, 2) == 3
    assert add_numbers(5, 5) == 10 