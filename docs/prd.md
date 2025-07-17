# 【POC 需求说明】—「古籍竖排简体文字生成工具」
版本：v0.2 日期：YYYY-MM-DD

## 1. 目标
在 7 天内交付一条最小可运行链路：
输入「扫描版单页 PDF（300 DPI，A4 以内）」
→ 输出「竖排简体列（可搜索文字，列数、字数与原书一致）」PDF。

## 2. 范围（仅保留关键功能）
- P0 PDF 拆页与基本信息读取
  - 将扫描版 PDF 拆为单页光栅图（默认 400 DPI，可通过 `--dpi` 覆盖），获取 DPI / 页面尺寸。
- P1 图像预处理
  - 灰度化、二值化，可选倾斜校正（手动参数）。
- P2 列检测与裁切
  - 支持检测 2–6 列，误差可接受 ≤ ±2 字宽。
- P3 竖排 OCR（繁体输出，det + cls + rec 全流水线）
  - 基于 PaddleOCR `predict()` 方法，一次完成方向分类、文字检测与识别，目标正确率 ≥ 80%（示范页）。
- P4 繁→简体转换
  - 使用 OpenCC，确保转换后字符数不变。
- P5 竖排排版（简体文字）
  - 输出 PDF，仅包含竖排简体文字，列数、每列字数及列间距需与原书保持一致。
  - 简体文字可全文搜索。
- P6 CLI 验证命令
  - `boocr poc --input <in.pdf> --output <out.pdf>`：完整 P0–P5 流程
  - `boocr extract [--input <in.pdf>] [--dpi 400]`：仅执行 P0，拆页 PNG 自动输出至 `output/<PDF名>/P0/`（省略 --input 时自动选择 input/ 目录下唯一且未处理过的 PDF）
  - `boocr preproc [--input <in.pdf|output/<PDF名>/P0/>] [--dpi 400] [--deskew_angle <deg>]`：仅执行 P1；若未指定 input，则在 output 中自动寻找唯一 P0 目录
  - `boocr col [--input <in.pdf|output/<PDF名>/P1/>] [--columns <n>] [--dpi 400] [--save_crops]`：仅执行 P2，输出列分割 JSON、预览 PNG；若 `--save_crops` 则额外保存列裁剪 PNG 至 `output/<PDF名>/P2/`
  - 两条命令均运行完毕终端提示 "DONE" 并返回码 0。
  - 所有 CLI 子命令（extract / preproc / col / poc）在成功结束时均应打印 "DONE" 并返回码 0，错误时返回非零并友好提示。

【删除/延迟的功能】
- 多页批处理与断点续跑
- meta.json、日志彩色美化
- 性能与资源指标、异常恢复
- GUI、安装脚本、CI/CD

## 3. 输入 / 输出规格
- 输入：扫描版单页 PDF，300 DPI，A4 以内。
- 输出（完整流程）：`page_simplified.pdf`，尺寸与输入相同，竖排简体文字可复制/搜索。
- 输出（仅 P0）：`output/<PDF名>/P0/page_<n>.png`，PNG 清晰度与 400 DPI 原图近似。

## 4. 验收标准
- A. 样例图片（提供 3 页）全部生成对应的单列/多列简体文字 PDF。
- B. 目测 OCR 准确率 ≧ 80%，排版正确（列数、分列位置）。
- C. 生成 PDF 中每列字数与原书对应列一致，且可全文搜索。
- D. 终端无未捕获异常，返回码 0。

## 5. 里程碑（7 天）
- D1（+1 天） 项目骨架 & CLI 雏形
- D2（+3 天） PDF 拆页 + 图像预处理 + 列检测可视化
- D3（+5 天） OCR + 繁→简转换 + 坐标映射贯通
- D4（+7 天） 双列 PDF 排版输出 & 简要文档
