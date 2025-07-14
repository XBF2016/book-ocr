"""
列检测与裁切
"""
from typing import List, Tuple

import numpy as np


def detect_columns(bin_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    从二值化后的页面图像中检测文本列的边界。

    Args:
        bin_image: 二值化后的图像，其中文本为黑色 (0)，背景为白色 (255)。
                   形状为 (H, W)。

    Returns:
        一个列表，每个元素是一个元组，代表一列的边界框 (x1, y1, x2, y2)。
        目前 y1, y2 直接使用页面高度。
    """
    height, width = bin_image.shape
    # T17.2: 实现垂直投影
    # invert image, so text is 1 and background is 0
    inv_image = 255 - bin_image
    # Sum along the vertical axis to get the projection profile
    # The result is a 1D array where each value is the sum of pixels in that column.
    vertical_projection = np.sum(inv_image, axis=0) // 255 # a bit easier to reason about

    # T17.3: Find column boundaries from the projection
    # Use a simple threshold to find columns. Any projection > 0 is considered part of a column.
    # This is a simple but effective method for well-separated columns.
    threshold = 0
    is_text_column = vertical_projection > threshold

    # Find where columns start and end
    # A column starts when we transition from False to True
    # A column ends when we transition from True to False
    is_text_column_shifted = np.roll(is_text_column, 1)
    is_text_column_shifted[0] = False # The first element has no left neighbor

    starts = np.where(~is_text_column_shifted & is_text_column)[0]
    ends = np.where(is_text_column_shifted & ~is_text_column)[0]

    # Handle edge case where the last column extends to the edge of the image
    if len(starts) > len(ends):
        ends = np.append(ends, width)

    if len(starts) == 0:
        return []

    # Create bounding boxes
    bboxes = []
    for start_x, end_x in zip(starts, ends):
        # We can add some filtering here, e.g., for very thin columns
        min_col_width = 10 # pixels
        if end_x - start_x > min_col_width:
            bboxes.append((start_x, 0, end_x, height))

    return bboxes
