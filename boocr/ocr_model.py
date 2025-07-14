#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR 模型下载和缓存管理模块。
负责检测模型是否已下载，自动下载缺失的模型，以及管理模型缓存。
"""

import os
import sys
import logging
import hashlib
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

# 必要的依赖
import requests
from tqdm import tqdm
import paddle

# 配置日志
logger = logging.getLogger(__name__)

# PaddleOCR 默认缓存路径
DEFAULT_MODEL_PATH = os.path.expanduser(os.path.join("~", ".paddleocr"))

# 模型配置信息：各种模型的远程URL、本地路径、校验哈希
# 竖排繁体中文模型信息
VERTICAL_CHT_MODELS = {
    # 文本检测模型
    "det": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_infer.tar",
        "path": os.path.join(DEFAULT_MODEL_PATH, "det", "ch"),
        "md5": "91c5c1aa5bcb72ab111c599440df7d75",
        "filename": "ch_PP-OCRv4_det_infer.tar",
    },
    # 文本方向分类器
    "cls": {
        "url": "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar",
        "path": os.path.join(DEFAULT_MODEL_PATH, "cls", "ch"),
        "md5": "1a9e0132d311ac93ea578286f0604ce5",
        "filename": "ch_ppocr_mobile_v2.0_cls_infer.tar",
    },
    # 繁体中文文本识别模型
    "rec": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese_cht/ch_PP-OCRv4_rec_infer.tar",
        "path": os.path.join(DEFAULT_MODEL_PATH, "rec", "ch_cht"),
        "md5": "4e9a5ff87e47c41371d4eae45da6f51b",
        "filename": "ch_PP-OCRv4_rec_infer.tar",
    }
}


class ModelManager:
    """
    PaddleOCR 模型管理器，负责：
    1. 检查模型是否已下载
    2. 下载缺失的模型
    3. 验证模型完整性
    4. 解压模型文件
    """
    def __init__(self, model_path: Optional[str] = None, verbose: bool = True):
        """
        初始化模型管理器

        Args:
            model_path: 模型存储路径，默认为 ~/.paddleocr
            verbose: 是否显示详细日志
        """
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.verbose = verbose

        # 创建模型目录（如果不存在）
        os.makedirs(self.model_path, exist_ok=True)

        # 检查 paddle 是否已安装
        self._check_paddle_installation()

    def _check_paddle_installation(self):
        """检查 Paddle 是否正确安装"""
        try:
            paddle_version = paddle.__version__
            logger.info(f"检测到 PaddlePaddle 版本: {paddle_version}")
        except ImportError:
            logger.error("未检测到 PaddlePaddle。请先安装 PaddlePaddle。")
            logger.info("安装命令: pip install paddlepaddle")
            raise RuntimeError("PaddlePaddle 未安装")

    def _download_file(self, url: str, save_path: str) -> bool:
        """
        从URL下载文件并显示进度条

        Args:
            url: 下载文件的URL
            save_path: 保存路径

        Returns:
            bool: 下载是否成功
        """
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 KB

            # 创建保存目录
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            desc = f"下载 {os.path.basename(url)}"
            with open(save_path, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=desc,
                disable=not self.verbose
            ) as pbar:
                for data in response.iter_content(block_size):
                    f.write(data)
                    pbar.update(len(data))

            return True
        except Exception as e:
            logger.error(f"下载失败: {url}, 错误: {e}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return False

    def _verify_md5(self, file_path: str, expected_md5: str) -> bool:
        """
        验证文件的MD5哈希值

        Args:
            file_path: 文件路径
            expected_md5: 期望的MD5哈希

        Returns:
            bool: 哈希是否匹配
        """
        if not os.path.exists(file_path):
            return False

        try:
            with open(file_path, 'rb') as f:
                file_md5 = hashlib.md5(f.read()).hexdigest()

            return file_md5 == expected_md5
        except Exception as e:
            logger.error(f"MD5验证失败: {file_path}, 错误: {e}")
            return False

    def _extract_tar(self, tar_path: str, extract_dir: str) -> bool:
        """
        解压tar文件

        Args:
            tar_path: tar文件路径
            extract_dir: 解压目录

        Returns:
            bool: 解压是否成功
        """
        try:
            import tarfile

            # 创建解压目录
            os.makedirs(extract_dir, exist_ok=True)

            with tarfile.open(tar_path) as tar:
                tar.extractall(path=extract_dir)

            return True
        except Exception as e:
            logger.error(f"解压失败: {tar_path}, 错误: {e}")
            return False

    def is_model_downloaded(self, model_type: str = "det", lang: str = "ch_cht") -> bool:
        """
        检查模型是否已下载并解压

        Args:
            model_type: 模型类型，可选值: det, cls, rec
            lang: 语言，可选值: ch, ch_cht

        Returns:
            bool: 模型是否已下载并解压
        """
        # 确定模型信息
        if model_type == "det":
            model_info = VERTICAL_CHT_MODELS["det"]
        elif model_type == "cls":
            model_info = VERTICAL_CHT_MODELS["cls"]
        elif model_type == "rec":
            if lang == "ch_cht":
                model_info = VERTICAL_CHT_MODELS["rec"]
            else:
                # 默认使用简体中文
                model_info = VERTICAL_CHT_MODELS["rec"]
        else:
            logger.error(f"不支持的模型类型: {model_type}")
            return False

        # 检查模型文件夹是否存在
        model_dir = model_info["path"]
        if not os.path.exists(model_dir):
            return False

        # 检查模型文件是否存在
        # PaddleOCR 模型解压后通常包含 inference.pdmodel 和 inference.pdiparams 文件
        model_files = os.listdir(model_dir)
        required_files = ["inference.pdmodel", "inference.pdiparams"]

        for req_file in required_files:
            if not any(req_file in file for file in model_files):
                return False

        return True

    def download_model(self, model_type: str = "det", lang: str = "ch_cht") -> bool:
        """
        下载并解压指定的模型

        Args:
            model_type: 模型类型，可选值: det, cls, rec
            lang: 语言，可选值: ch, ch_cht

        Returns:
            bool: 模型下载和解压是否成功
        """
        # 确定模型信息
        if model_type == "det":
            model_info = VERTICAL_CHT_MODELS["det"]
        elif model_type == "cls":
            model_info = VERTICAL_CHT_MODELS["cls"]
        elif model_type == "rec":
            if lang == "ch_cht":
                model_info = VERTICAL_CHT_MODELS["rec"]
            else:
                # 默认使用简体中文
                model_info = VERTICAL_CHT_MODELS["rec"]
        else:
            logger.error(f"不支持的模型类型: {model_type}")
            return False

        # 创建下载目录
        download_dir = os.path.join(self.model_path, "download")
        os.makedirs(download_dir, exist_ok=True)

        # 下载文件路径
        file_name = model_info["filename"]
        file_path = os.path.join(download_dir, file_name)

        # 下载模型
        logger.info(f"下载模型: {model_type} ({lang})")
        success = self._download_file(model_info["url"], file_path)
        if not success:
            return False

        # 验证MD5
        if not self._verify_md5(file_path, model_info["md5"]):
            logger.error(f"模型文件MD5验证失败: {file_path}")
            return False

        # 解压模型
        logger.info(f"解压模型: {file_path}")
        extract_dir = model_info["path"]
        os.makedirs(extract_dir, exist_ok=True)

        success = self._extract_tar(file_path, extract_dir)
        if not success:
            return False

        logger.info(f"模型 {model_type} ({lang}) 已成功下载并解压")
        return True

    def ensure_all_models(self, lang: str = "ch_cht") -> bool:
        """
        确保所有必需的模型都已下载并准备就绪

        Args:
            lang: 语言，可选值: ch, ch_cht

        Returns:
            bool: 所有模型是否已准备就绪
        """
        all_ready = True

        # 检查并下载检测模型
        if not self.is_model_downloaded("det"):
            logger.info("检测模型未下载，开始下载...")
            all_ready &= self.download_model("det")

        # 检查并下载分类模型
        if not self.is_model_downloaded("cls"):
            logger.info("分类模型未下载，开始下载...")
            all_ready &= self.download_model("cls")

        # 检查并下载识别模型
        if not self.is_model_downloaded("rec", lang):
            logger.info(f"{lang} 识别模型未下载，开始下载...")
            all_ready &= self.download_model("rec", lang)

        return all_ready

    def get_model_dir(self, model_type: str = "det", lang: str = "ch_cht") -> str:
        """
        获取模型目录路径

        Args:
            model_type: 模型类型，可选值: det, cls, rec
            lang: 语言，可选值: ch, ch_cht

        Returns:
            str: 模型目录路径
        """
        if model_type == "det":
            return VERTICAL_CHT_MODELS["det"]["path"]
        elif model_type == "cls":
            return VERTICAL_CHT_MODELS["cls"]["path"]
        elif model_type == "rec":
            if lang == "ch_cht":
                return VERTICAL_CHT_MODELS["rec"]["path"]
            else:
                # 默认使用简体中文
                return VERTICAL_CHT_MODELS["rec"]["path"]
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")

# 工具函数：确保模型已下载
def ensure_models_ready(verbose: bool = True) -> bool:
    """
    确保所有必需的PaddleOCR模型都已下载并准备就绪

    Args:
        verbose: 是否显示详细日志

    Returns:
        bool: 所有模型是否已准备就绪
    """
    manager = ModelManager(verbose=verbose)
    return manager.ensure_all_models()

# 命令行工具
def main():
    """命令行入口：下载并验证模型"""
    import argparse

    parser = argparse.ArgumentParser(description="PaddleOCR 模型下载工具")
    parser.add_argument("--lang", default="ch_cht", choices=["ch", "ch_cht"],
                        help="选择语言模型 (ch: 简体中文, ch_cht: 繁体中文)")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    args = parser.parse_args()

    # 配置日志
    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=log_level, format='%(message)s')

    print(f"开始下载 PaddleOCR {args.lang} 模型...")
    manager = ModelManager(verbose=not args.quiet)
    success = manager.ensure_all_models(args.lang)

    if success:
        print("所有模型已成功下载并准备就绪。")
        return 0
    else:
        print("部分或全部模型下载失败，请检查网络连接后重试。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
