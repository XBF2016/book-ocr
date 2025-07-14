"""
Tests for column detection functionality.
"""
import cv2
import pytest
from pathlib import Path
import numpy as np

from boocr.col_detect import detect_columns
from boocr.image_proc import to_grayscale, otsu_binarize

# 获取当前文件所在的目录，从而构建资源文件的绝对路径
# 这使得无论在哪里运行 pytest，都能找到测试资源
_current_dir = Path(__file__).parent.resolve()
ASSETS_DIR = _current_dir / "assets"

@pytest.fixture
def sample_image_binarized() -> np.ndarray:
    """Fixture to load and binarize a sample image."""
    img_path = ASSETS_DIR / "test.jpeg"
    assert img_path.exists(), f"Test image not found at {img_path}"

    # 使用 cv2.imdecode 来处理可能包含非 ASCII 字符的路径
    img_bytes = np.fromfile(img_path, dtype=np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    assert img is not None, "Failed to load image"

    gray_img = to_grayscale(img)
    bin_img = otsu_binarize(gray_img)
    return bin_img

def test_detect_columns_auto(sample_image_binarized):
    """
    Test automatic column detection.
    It should find a plausible number of columns in the sample image.
    """
    bboxes = detect_columns(sample_image_binarized)

    # 根据 test.jpeg 的目测，它应该是多栏的。
    # 我们设置一个合理的范围，例如，至少有5栏，但不多于20栏。
    # 这是一个健壮性测试，而不是精确性测试。
    assert 5 < len(bboxes) < 20

    # 检查返回的第一个 bbox 是否格式正确
    assert isinstance(bboxes[0], tuple)
    assert len(bboxes[0]) == 4


def test_detect_columns_manual_override(sample_image_binarized):
    """
    Test manual column override.
    It should return exactly the number of columns specified.
    """
    num_cols_manual = 10
    bboxes = detect_columns(sample_image_binarized, num_columns=num_cols_manual)

    assert len(bboxes) == num_cols_manual

    # 检查第一个和最后一个 bbox 的坐标是否合理
    height, width = sample_image_binarized.shape
    first_bbox = bboxes[0]
    last_bbox = bboxes[-1]

    # 第一个 bbox 应该从 x=0 开始
    assert first_bbox[0] == 0
    # 最后一个 bbox 应该在 x=width 结束
    assert last_bbox[2] == width
    # 所有 bbox 的 y 坐标应该覆盖整个高度
    assert first_bbox[1] == 0
    assert first_bbox[3] == height
