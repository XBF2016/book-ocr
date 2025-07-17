#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR module for vertical Chinese text recognition using PaddleOCR.
Support for traditional Chinese characters with vertical layout.
"""

import os
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any
import inspect
from functools import lru_cache

# PaddleOCR相关导入
from paddleocr import PaddleOCR

# 仅识别模型 (TextRecognition) - PaddleOCR ≥3.0
try:
    from paddleocr import TextRecognition  # type: ignore
except ImportError:
    TextRecognition = None  # 动态检查

# Import project specific modules
from boocr.dataclasses import ColumnCrop, OcrResult
from boocr.ocr_model import ensure_models_ready, ModelManager

# 配置日志
logger = logging.getLogger(__name__)

# 当列图像过高（长边 >> 短边）时，按该高度切分进行分段OCR
MAX_SEGMENT_HEIGHT = 1024  # 像素，可根据需要调整


class VerticalChineseOCR:
    """
    竖排繁体中文OCR引擎封装，基于PaddleOCR。
    """
    def __init__(
        self,
        use_gpu: bool = False,
        gpu_mem: int = 500,
        enable_mkldnn: bool = True,
        cpu_threads: int = 4,
        lang_type: str = "chinese_cht",  # 繁体中文模型
        auto_download: bool = True,      # 自动下载模型
        det_model_dir: str | None = None,
        rec_model_dir: str | None = None,
        cls_model_dir: str | None = None,
        rec_only: bool = False,
    ):
        """
        初始化OCR引擎

        Args:
            use_gpu: 是否使用GPU
            gpu_mem: GPU内存大小(MB)
            enable_mkldnn: 是否启用mkldnn加速
            cpu_threads: CPU线程数
            lang_type: 语言类型，默认为繁体中文(chinese_cht)
            auto_download: 是否自动下载模型（如果不存在）
        """
        logger.info(f"初始化竖排繁体OCR引擎，使用语言模型: {lang_type}")

        # 如果自动下载模型开关打开，确保模型已下载
        if auto_download:
            self._ensure_models()

        try:
            # PaddleOCR 3.x 起移除了 det/rec/cls/use_gpu 等旧参数，改为统一的
            # device / use_textline_orientation / text_det_* 命名。这里按新接口
            # 进行初始化，确保向前兼容。

            # 保存模式开关供后续逻辑使用
            self.rec_only: bool = rec_only

            device = "gpu" if use_gpu else "cpu"

            # 若指定了自定义模型目录，注入对应参数
            # 根据 rec_only 开关动态注入参数
            extra_args: dict[str, str | bool] = {}
            if det_model_dir:
                extra_args["det_model_dir"] = str(det_model_dir)
            if rec_model_dir:
                extra_args["rec_model_dir"] = str(rec_model_dir)
                # 解析 inference.yml 以取得 model_name，避免 name mismatch
                try:
                    cfg_path = Path(rec_model_dir) / "inference.yml"
                    if cfg_path.exists():
                        import yaml  # PyYAML
                        with cfg_path.open("r", encoding="utf-8") as f:
                            cfg = yaml.safe_load(f)
                        model_name_in_cfg = cfg.get("Global", {}).get("model_name")
                        if model_name_in_cfg:
                            extra_args["text_recognition_model_name"] = model_name_in_cfg
                except Exception as _e:
                    logger.debug(f"无法解析 rec 模型 inference.yml: {_e}")
            if cls_model_dir:
                extra_args["cls_model_dir"] = str(cls_model_dir)



            self.ocr = PaddleOCR(
                # 基本语言 & 竖排方向识别
                lang=lang_type,
                use_textline_orientation=True,  # 竖排方向分类

                # 文本检测阈值配置（对应旧 det_db_*）
                text_det_thresh=0.3,
                text_det_box_thresh=0.5,
                text_det_unclip_ratio=1.6,

                # 运行设备与性能参数
                device=device,
                enable_mkldnn=enable_mkldnn,
                cpu_threads=cpu_threads,
                **extra_args,
            )
            self.initialized = True
            logger.info("OCR引擎初始化成功")
        except Exception as e:
            logger.error(f"OCR引擎初始化失败: {e}")
            self.initialized = False
            raise RuntimeError(f"OCR引擎初始化失败: {e}")

    def _ensure_models(self):
        """确保所需的模型已经下载并准备就绪"""
        logger.info("检查 PaddleOCR 模型...")

        try:
            # 使用我们的自定义下载器确保模型已准备就绪
            models_ready = ensure_models_ready()
            if not models_ready:
                logger.error("模型下载或校验失败，终止初始化")
                raise RuntimeError("PaddleOCR 模型缺失或校验失败，无法初始化 OCR 引擎。请检查网络或手动更新 MD5。")
            else:
                logger.info("所有模型已准备就绪")
        except Exception as e:
            logger.error(f"模型检查流程异常: {e}")
            # 直接抛出异常，阻止后续流程
            raise

    def is_initialized(self) -> bool:
        """检查OCR引擎是否已初始化"""
        return hasattr(self, 'initialized') and self.initialized

    def _save_debug_patch(self, patch_img, column_crop):
            """
            Save the first few patch images to disk when running with DEBUG log level.
            This helps developers visually inspect what content is being fed into the
            recognizer during patch-wise OCR.
            """
            try:
                import cv2
                from pathlib import Path



                # Create counter on the fly (instance level)
                if not hasattr(self, "_debug_patch_cnt"):
                    self._debug_patch_cnt = 0
                if self._debug_patch_cnt >= 20:
                    return

                # Skip empty patches that could cause cv2 errors
                if patch_img.size == 0:
                    return

                debug_dir = Path("debug_patches")
                debug_dir.mkdir(parents=True, exist_ok=True)

                fname = (
                    f"page_{column_crop.page_index + 1}_col_{column_crop.column_index + 1}_patch_{self._debug_patch_cnt + 1}.png"
                )
                cv2.imwrite(str(debug_dir / fname), patch_img)
                logger.debug(f"[DEBUG_PATCH] Saved {fname}")
                self._debug_patch_cnt += 1
            except Exception as _e:
                # Failure to save debug image should not affect main flow
                logger.debug(f"保存 debug patch 失败: {_e}")

    def run_ocr(self, column_crop: ColumnCrop) -> OcrResult:
        """
        对裁剪的列图像执行OCR识别

        Args:
            column_crop: 从页面裁剪的单列图像

        Returns:
            OcrResult: OCR识别结果，包含识别的文本和置信度
        """
        if not self.is_initialized():
            raise RuntimeError("OCR引擎未初始化")

        # 执行OCR
        try:
            import cv2  # 局部导入避免无用依赖
            # PaddleOCR 期望输入为BGR/RGB三通道图像。
            img = column_crop.image
            if img.ndim == 2:
                # 灰度或二值图 -> BGR
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            # 若列图像太窄（短边 < 200px），则放大到 200px，避免 "无文本" 早停
            h, w = img.shape[:2]
            if min(h, w) < 200:
                scale = 200 / min(h, w)
                img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            # Debug: save full column image for manual inspection
            try:
                from pathlib import Path
                debug_col_dir = Path("debug_columns")
                debug_col_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(debug_col_dir / f"page_{column_crop.page_index + 1}_col_{column_crop.column_index + 1}.png"), img)
            except Exception as _e:
                logger.debug("保存 debug 列图失败: %s", _e)

            # ---------- 分段 OCR 逻辑 ----------
            # 当 rec_only 模式启用时，直接使用纯识别路径，跳过检测/方向分类
            if getattr(self, "rec_only", False):
                try:
                    import cv2

                    # PaddleOCR 的 rec 网络期望横排文本，故将竖排图旋转 90° 使其横向
                    horiz = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    def _rec_only(arr):
                        """仅识别文字，不进行检测/分类"""
                        try:
                            fn = self.ocr.predict if hasattr(self.ocr, "predict") else self.ocr.ocr
                            sig = inspect.signature(fn)
                            kwargs = {}
                            if "det" in sig.parameters:
                                kwargs["det"] = False
                            if "rec" in sig.parameters:
                                kwargs["rec"] = True
                            if "cls" in sig.parameters:
                                kwargs["cls"] = False
                            return fn(arr, **kwargs) if kwargs else fn(arr)
                        except Exception as _e:
                            logger.error(f"rec-only 调用失败: {_e}")
                            return None

                    # -------- 新增：按宽度 PATCH_W 切块识别 --------
                    # 直接对整幅旋转后的图像做识别，不再做横向切块
                    tried_directions = [horiz, cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)]
                    for horiz in tried_directions:
                        rec_res = _rec_only(horiz)
                        logger.debug("rec_res=%s", rec_res)
                        if not rec_res:
                            continue

                        parts: list[str] = []
                        if isinstance(rec_res, list):
                            for elem in rec_res:
                                if isinstance(elem, dict) and "rec_text" in elem:
                                    parts.append(elem["rec_text"])
                                elif isinstance(elem, (list, tuple)):
                                    # PaddleOCR 旧版返回 (text, ((bbox), score))
                                    if len(elem) >= 2 and isinstance(elem[0], str):
                                        parts.append(elem[0])
                        full_text = "".join(parts)
                        if full_text:
                            return OcrResult(
                                page_index=column_crop.page_index,
                                column_index=column_crop.column_index,
                                text=full_text,
                                confidence=0.5,
                            )
                    if full_text:
                        return OcrResult(
                            page_index=column_crop.page_index,
                            column_index=column_crop.column_index,
                            text=full_text,
                            confidence=0.5,
                        )
                except Exception as _e:
                    logger.error(f"rec_only 纯识别路径失败: {_e}")

                # 若 rec_only 仍未识别到文本，则继续走后续兜底逻辑（TextRecognition 等）

            def _paddle_predict(img_arr):
                """包装 PaddleOCR 推理，兼容 .ocr / .predict 接口"""
                try:
                    if hasattr(self.ocr, "ocr"):
                        # 新旧版本 PaddleOCR API 兼容：部分版本 .ocr() 不接受 cls 参数
                        try:
                            sig = inspect.signature(self.ocr.ocr)
                            if "cls" in sig.parameters:
                                return self.ocr.ocr(img_arr, cls=True)
                            else:
                                return self.ocr.ocr(img_arr)
                        except (ValueError, TypeError):
                            # 无法获取签名时，直接尝试不带 cls
                            return self.ocr.ocr(img_arr)
                    elif hasattr(self.ocr, "predict"):
                        # 同理，predict() 在新版本已不再接受 cls
                        try:
                            sig = inspect.signature(self.ocr.predict)
                            kwargs = {"det": True, "rec": True}
                            if "cls" in sig.parameters:
                                kwargs["cls"] = True
                            return self.ocr.predict(img_arr, **kwargs)
                        except (ValueError, TypeError):
                            # 若无法检测参数，使用最小必需参数
                            return self.ocr.predict(img_arr, det=True, rec=True)
                    else:
                        logger.error("未找到可用的 OCR 推理接口 (.ocr / .predict)")
                        return None
                except Exception as _e:
                    logger.error(f"PaddleOCR 运行失败: {_e}")
                    return None

            def _run_with_rotation(img_arr):
                """执行推理，并在检测为空时尝试旋转90°/270°容错"""
                res = _paddle_predict(img_arr)
                if (not res) or (len(res[0]) == 0):
                    img_rot = cv2.rotate(img_arr, cv2.ROTATE_90_CLOCKWISE)
                    res = _paddle_predict(img_rot)
                    if (not res) or (len(res[0]) == 0):
                        img_rot = cv2.rotate(img_arr, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        res = _paddle_predict(img_rot)
                return res

            segments = []  # (y_offset, result_list) 保存每段识别结果

            # 提前触发切块：只要高度超过阈值即分段
            if h > MAX_SEGMENT_HEIGHT:
                # 高度过大时按 MAX_SEGMENT_HEIGHT 切块上采样
                for y in range(0, h, MAX_SEGMENT_HEIGHT):
                    seg_img = img[y : min(y + MAX_SEGMENT_HEIGHT, h), :]
                    res = _run_with_rotation(seg_img)
                    segments.append((y, res))
            else:
                # 图像高度可接受，直接整体识别
                res = _run_with_rotation(img)
                segments.append((0, res))

            # ---------------- 结果合并 ----------------
            texts_with_pos = []  # (center_y, text, conf)
            for y_offset, seg_res in segments:
                if (not seg_res) or len(seg_res) == 0 or len(seg_res[0]) == 0:
                    continue

                for line in seg_res[0]:
                    if len(line) >= 2 and isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                        bbox, (text, confidence) = line
                        # 计算该行 bbox 中心的全局 y 坐标（加 offset）
                        try:
                            ys = [pt[1] for pt in bbox]
                            center_y = (sum(ys) / len(ys)) + y_offset
                        except Exception:
                            center_y = y_offset
                        texts_with_pos.append((center_y, text, float(confidence)))

            if not texts_with_pos:
                # --- Fallback: patch-wise rec-only 模式 ---
                logger.info("初次 OCR 未识别到文本，尝试 patchwise rec-only 容错 ...")
                try:
                    import cv2
                    horiz = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    def _rec_only(arr):
                        """仅识别，不做检测；根据函数签名决定可传参"""
                        try:
                            fn = self.ocr.predict if hasattr(self.ocr, "predict") else self.ocr.ocr
                            sig = inspect.signature(fn)
                            kwargs = {}
                            if "det" in sig.parameters:
                                kwargs["det"] = False
                            if "rec" in sig.parameters:
                                kwargs["rec"] = True
                            if "cls" in sig.parameters:
                                kwargs["cls"] = False
                            return fn(arr, **kwargs) if kwargs else fn(arr)
                        except Exception as _e:
                            logger.debug(f"rec-only 调用失败: {_e}")
                            return None

                    # 分段识别，按 PATCH_W 切块并重叠 OVERLAP 避免截断字符
                    PATCH_W = 320
                    OVERLAP = 64
                    h_r, w_r = horiz.shape[:2]
                    parts: list[str] = []
                    step = max(PATCH_W - OVERLAP, 1)
                    for x0 in range(0, w_r, step):
                        x1 = min(x0 + PATCH_W, w_r)
                        patch = horiz[:, x0:x1]
                        if patch.size == 0:
                            continue
                        rec_res = _rec_only(patch)
                        if not rec_res:
                            continue
                        if isinstance(rec_res, list):
                            for elem in rec_res:
                                if isinstance(elem, dict) and "rec_text" in elem:
                                    parts.append(elem["rec_text"])
                                elif isinstance(elem, (list, tuple)):
                                    if len(elem) >= 2:
                                        if isinstance(elem[0], str):
                                            parts.append(elem[0])
                                        elif isinstance(elem[1], (list, tuple)) and len(elem[1]) >= 1:
                                            parts.append(elem[1][0])
                    full_text = "".join(parts)
                    if full_text:
                        return OcrResult(
                            page_index=column_crop.page_index,
                            column_index=column_crop.column_index,
                            text=full_text,
                            confidence=0.5,
                        )
                except Exception as _e:
                    logger.debug("patchwise rec-only 容错失败: %s", _e)

                # --- 第二层兜底：使用 TextRecognition 纯 rec 模型 ---
                if TextRecognition is not None:
                    try:
                        @lru_cache(maxsize=1)
                        def _get_trad_rec_model():
                            return TextRecognition(model_name="chinese_cht_PP-OCRv3_mobile_rec")

                        rec_model = _get_trad_rec_model()
                        import cv2
                        img_rot = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                        # PaddleOCR 会自动缩放超长边; 但我们可手动限制宽度 4000
                        h_r, w_r = img_rot.shape[:2]
                        if w_r > 4000:
                            scale = 4000 / w_r
                            img_rot = cv2.resize(img_rot, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

                        # --- 按宽度 PATCH_WIDTH 切块识别，解决超长文本 ---
                        PATCH_W = 320
                        parts = []
                        for x0 in range(0, w_r, PATCH_W):
                            patch = img_rot[:, x0 : min(x0 + PATCH_W, w_r)]
                            if patch.size == 0:
                                continue
                            rec_res = rec_model.predict(patch)
                            if not rec_res:
                                continue
                            for item in rec_res:
                                if hasattr(item, "rec_text"):
                                    parts.append(item.rec_text)
                        full_text = "".join(parts)
                        if full_text:
                            return OcrResult(
                                page_index=column_crop.page_index,
                                column_index=column_crop.column_index,
                                text=full_text,
                                confidence=0.6,
                            )
                    except Exception as e:
                        logger.error(f"TextRecognition 纯识别兜底失败: {e}")

                logger.warning(f"页面 {column_crop.page_index} 列 {column_crop.column_index} OCR未识别到文本")
                return OcrResult(
                    page_index=column_crop.page_index,
                    column_index=column_crop.column_index,
                    text="",
                    confidence=0.0,
                )

            # 按 y 坐标降序（底 -> 顶）排序，符合竖排阅读顺序
            texts_with_pos.sort(key=lambda item: item[0], reverse=True)

            texts = [t for _, t, _ in texts_with_pos]
            confidences = [c for _, _, c in texts_with_pos]

            full_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return OcrResult(
                page_index=column_crop.page_index,
                column_index=column_crop.column_index,
                text=full_text,
                confidence=avg_confidence,
            )

        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return OcrResult(
                page_index=column_crop.page_index,
                column_index=column_crop.column_index,
                text="",
                confidence=0.0,
            )

    def process_columns(self, columns: List[ColumnCrop]) -> List[OcrResult]:
        """
        批量处理多个列图像

        Args:
            columns: 列图像列表

        Returns:
            List[OcrResult]: OCR识别结果列表
        """
        results = []
        for column in columns:
            try:
                result = self.run_ocr(column)
                results.append(result)
            except Exception as e:
                logger.error(f"处理列 {column.page_index}-{column.column_index} 失败: {e}")
                # 添加空结果以保持索引一致性
                results.append(OcrResult(
                    page_index=column.page_index,
                    column_index=column.column_index,
                    text="",
                    confidence=0.0
                ))

        return results


# 工厂方法：创建OCR引擎实例
def create_ocr_engine(
    use_gpu: bool = False,
    auto_download: bool = True,
    det_model_dir: str | None = None,
    rec_model_dir: str | None = None,
    cls_model_dir: str | None = None,
    rec_only: bool = False,
) -> VerticalChineseOCR:
    """
    创建竖排繁体中文OCR引擎实例

    Args:
        use_gpu: 是否使用GPU加速
        auto_download: 是否自动下载模型（如果不存在）

    Returns:
        VerticalChineseOCR: OCR引擎实例
    """
    return VerticalChineseOCR(
        use_gpu=use_gpu,
        lang_type="chinese_cht",  # 使用繁体中文模型
        auto_download=auto_download,
        det_model_dir=det_model_dir,
        rec_model_dir=rec_model_dir,
        cls_model_dir=cls_model_dir,
        rec_only=rec_only,
    )


# T23: 封装函数，直接传入图像数组并获取识别的文本
def run_ocr(crop: np.ndarray) -> str:
    """
    对图像进行OCR识别，提取文本内容

    Args:
        crop: 图像数组(numpy.ndarray)，支持灰度或RGB格式

    Returns:
        str: 识别出的文本内容，如果识别失败则返回空字符串
    """
    try:
        # 创建OCR引擎（关闭自定义模型下载，直接交给 PaddleOCR 默认流程）
        ocr_engine = create_ocr_engine(use_gpu=False, auto_download=False)

        # 检查OCR引擎是否初始化成功
        if not ocr_engine.is_initialized():
            logger.error("OCR引擎初始化失败")
            return ""

        # PaddleOCR 要求三通道；若传入灰度，先转换
        img = crop
        if img.ndim == 2:
            import cv2
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # 兼容新旧 PaddleOCR API
        if hasattr(ocr_engine.ocr, "ocr"):
            try:
                sig = inspect.signature(ocr_engine.ocr.ocr)
                if "cls" in sig.parameters:
                    result = ocr_engine.ocr.ocr(img, cls=True)
                else:
                    result = ocr_engine.ocr.ocr(img)
            except (ValueError, TypeError):
                result = ocr_engine.ocr.ocr(img)
        else:
            try:
                sig = inspect.signature(ocr_engine.ocr.predict)
                kwargs = {"det": True, "rec": True}
                if "cls" in sig.parameters:
                    kwargs["cls"] = True
                result = ocr_engine.ocr.predict(img, **kwargs)
            except (ValueError, TypeError):
                result = ocr_engine.ocr.predict(img, det=True, rec=True)

        # 处理OCR结果
        if not result or len(result) == 0 or not result[0]:
            logger.warning("OCR未识别到文本")
            return ""

        # 提取文本并按从下到上的顺序合并（考虑竖排文字的阅读顺序）
        texts = []

        # PaddleOCR的结果格式: [[[文本框坐标], [文本, 置信度]], [...]]
        for line in result[0]:
            if len(line) >= 2 and isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                text = line[1][0]  # 提取文本
                texts.append(text)

        # 垂直文本，按从下到上的顺序合并
        full_text = "\n".join(reversed(texts))
        return full_text

    except Exception as e:
        logger.error(f"OCR识别失败: {e}")
        return ""
