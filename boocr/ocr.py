#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR module for vertical Chinese text recognition using PaddleOCR.
Support for traditional Chinese characters with vertical layout.
"""

import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple

# Import project specific modules
from boocr.dataclasses import ColumnCrop, OcrResult
