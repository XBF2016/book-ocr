# 【技术设计文档】—「古籍竖排繁‧简对照生成工具（POC）」
**版本：v0.3 日期：YYYY-MM-DD**

---
## 1. 总览
---
目标：在 7 天内完成单页竖排古籍扫描件（PDF/图像） → 「竖排简体列（可搜索文字，列数、字数与原书一致）」PDF 的最小可运行链路。
范围严格对标 PRD v0.2 (P0–P6)，排除批处理、GUI 等非必要功能。

---
## 2. 总体架构
---
```
CLI（入口层）
│
├─ Pipeline（业务编排层）
│  ├─ PdfSplitter        (P0)
│  ├─ Image Preprocessor (P1)
│  ├─ Column Detector    (P2)
│  ├─ Vertical OCR       (P3)
│  ├─ Trad→Simp Convert (P4)
│  └─ Vertical Text Render (P5)
│
└─ IO 层
   ├─ Input Loader  (PDF/图像读取与校验)
   └─ Output Composer (结果合成 PDF 并写盘)
```
**说明：**
• Pipeline 采用同步串行调用，保持代码直观、方便调试。
• 各子模块互相解耦，通过标准数据结构（见 3.2）传递。

---
## 3. 关键技术选型
---
### 3.1 语言与依赖
- **Python 3.11**（脚本快、生态丰富）
- **库**
  - `pdfplumber` / `PyPDF2` → PDF 拆页与光栅化 (P0)
  - `OpenCV`           → 图像处理 P1、P2
  - `numpy`            → 数值计算
  - `pytesseract` / `PaddleOCR` → 竖排繁体 OCR (P3)
  - `opencc-py`          → 繁→简转换 (P4)
  - `Pillow`             → 图像合成 (P5)
  - `reportlab` / `fpdf2`  → 可搜索 PDF 生成 (P5)
   `click` / `typer`        → CLI 解析 (P6)

### 3.2 数据结构约定（Python dataclass 简述）
- `InputSource`: `{path: str, type: 'pdf'|'image'}`
- `PageImage`: `ndarray`     # 输入全图
- `ColumnCrop`: `ndarray` + `bbox`  # 单列裁切结果
- `OcrResult`: `str`              # 单列繁体文本
- `RenderedPage`: `bytes`         # 内存中仅含简体文字的 PDF 页面对象
- `RenderConfig`: `{font_path: str, font_size: int, page_size: (w,h), gap_px: 20, …}`

### 3.3 核心算法
- **P0** 使用 `pdfplumber` 提取单页并光栅化为图像。
- **P1** 灰度化 + Otsu 二值化；倾斜校正可选手动角度参数。
- **P2** 垂直投影求列分割线；支持 2–6 列，误差控制≤±2 字宽。
- **P3** OCR：竖排模式，优先加载 PaddleOCR 的中日繁模型。
- **P4** OpenCC「t2s.json」配置，字符级转换，保持长度一致。
- **P5** 使用 `reportlab`/`fpdf2`，根据 OCR 结果的坐标信息，在对应位置直接绘制竖排的简体文字，确保文本可搜索且排版（列数、字数）与原书一致。
- **P6** CLI：`boocr poc --input <in.pdf> --output <page_simplified.pdf>`，运行完毕终端打印 "DONE"，异常捕获统一返回码 0。

---
## 4. 目录结构（建议）
---
```
book-ocr/
├─ boocr/            # Python package
│  ├─ cli.py         # 入口 (P6)
│  ├─ pipeline.py    # P0–P5 调度
│  ├─ pdf_utils.py   # P0
│  ├─ image_proc.py  # P1
│  ├─ col_detect.py  # P2
│  ├─ ocr.py         # P3
│  ├─ converter.py   # P4
│  └─ composer.py    # P5 (生成竖排简体文字 PDF)
├─ docs/             # PRD & 技术文档
└─ tests/            # 简单单元 / 样例图脚本
```

---
## 5. 里程碑与任务拆分（7 天）
---
- **D1**：仓库初始化、CLI 雏形、数据结构定义
- **D2**：`pdf_utils.py` (P0) + `image_proc.py` (P1) + `col_detect.py` (P2)，完成 PDF 拆页、预处理与列检测及可视化
- **D3**：`ocr.py` (P3) + `converter.py` (P4)，完成 OCR、繁简转换并贯通坐标映射
- **D4**：`composer.py` (P5) 完成竖排简体文字 PDF 生成；撰写 README 与交付文档
（每日 push + tag，保留回滚点）

---
## 6. 风险与缓解
---
- **竖排 OCR 准确率不足**：预留切换 Tesseract 方案；可人工校对示例页评估。
- **列检测偏差**：提供 CLI 手动列数参数覆盖自动检测。
- **字体兼容/嵌入问题**：默认提供开源可商用字体（如思源宋体）；如缺失则回退系统字体。
- **环境依赖安装**：提供 `requirements.txt` 与 FAQ。

---
## 7. 测试计划
---
- **单元测试**：每个模块核心函数 80% 覆盖率。
- **集成测试**：3 页示例 PDF，全链路跑通，断言输出 PDF 文件存在、非空且简体文字层可复制。
- **验收脚本**：`scripts/e2e.sh` / `.ps1` 一键执行，终端打印 DONE。

---
## 8. 交付物
---
1. 源码（含 `README`、`requirements.txt`）
2. 示例输入 PDF / 输出 PDF
3. 技术设计文档（本文）
4. 快速上手指南（CLI 使用示例）

---
## 9. 结语
---
本设计仅覆盖 POC 所需最小功能，后续扩展（多页、GUI 等）将在 POC 评审后另行规划。
