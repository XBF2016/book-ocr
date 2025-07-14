#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR模型下载和缓存功能
"""

import os
import pytest
import tempfile
import shutil

from boocr.ocr_model import ModelManager, ensure_models_ready

@pytest.mark.slow  # 标记为慢测试，因为涉及网络下载
class TestOcrModel:
    """测试OCR模型下载和缓存功能"""

    def test_model_manager_init(self):
        """测试ModelManager初始化"""
        # 使用临时目录，避免干扰实际环境
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ModelManager(model_path=temp_dir, verbose=False)
            assert manager is not None
            assert manager.model_path == temp_dir

    def test_is_model_downloaded(self):
        """测试检测模型是否已下载的功能"""
        # 使用临时目录，避免干扰实际环境
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ModelManager(model_path=temp_dir, verbose=False)

            # 新建临时目录应该没有模型
            assert manager.is_model_downloaded("det") is False
            assert manager.is_model_downloaded("cls") is False
            assert manager.is_model_downloaded("rec", lang="ch_cht") is False

    def test_get_model_dir(self):
        """测试获取模型目录路径"""
        # 使用临时目录，避免干扰实际环境
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ModelManager(model_path=temp_dir, verbose=False)

            # 检查路径是否正确拼接
            det_dir = manager.get_model_dir("det")
            cls_dir = manager.get_model_dir("cls")
            rec_dir = manager.get_model_dir("rec", "ch_cht")

            assert "det" in det_dir
            assert "cls" in cls_dir
            assert "rec" in rec_dir
            assert "ch_cht" in rec_dir

            # 非法的模型类型应该抛出异常
            with pytest.raises(ValueError):
                manager.get_model_dir("invalid_type")

    @pytest.mark.skipif("CI" in os.environ, reason="跳过在CI环境中的实际下载测试")
    def test_download_model_integration(self):
        """集成测试：实际下载模型文件（可选，因为文件很大）

        注意：此测试会实际下载模型，需要网络连接，且可能耗时较长
        """
        # 使用临时目录，避免干扰实际环境
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ModelManager(model_path=temp_dir, verbose=True)

            # 仅下载cls模型（相对较小）作为测试示例
            success = manager.download_model("cls")

            # 检查下载是否成功
            assert success is True
            assert manager.is_model_downloaded("cls") is True

if __name__ == "__main__":
    # 手动运行测试
    test = TestOcrModel()
    test.test_model_manager_init()
    test.test_is_model_downloaded()
    test.test_get_model_dir()
    print("基本测试通过!")

    # 如果想测试实际下载，请取消注释以下行
    # test.test_download_model_integration()
