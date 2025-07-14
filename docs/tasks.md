# 古籍竖排繁‧简对照生成工具 - 任务清单

→ 下一个任务：T07
提示：做完一个任务记得 **更新任务状态（√/□）和指针**

## 任务清单
（√＝已完成，□＝未完成）

### 基础准备
√ T01. 初始化本地 git 仓库：clone、创建 poc 分支，提交初始 README
√ T02. 创建 virtualenv 并写入 requirements.txt（Python 3.11 / click / typer / numpy / Pillow / OpenCV / opencc-py / paddleocr / pdfplumber / reportlab 等）

### 目录与骨架
√ T03. 在 tests/ 添加 pytest 初始化与示例占位文件
√ T04. 新建 boocr/ 包及空 __init__.py
√ T05. 创建 boocr/cli.py：click 入口 `boocr poc --input <in.pdf> --output <out.pdf>` 雏形（打印 "TODO"）
√ T06. 创建 boocr/pipeline.py：定义同步串行调用接口（空实现）
□ T07. 在 boocr/dataclasses.py 定义 InputSource / PageImage / ColumnCrop / OcrResult / RenderedPage / RenderConfig
□ T08. 更新 README：项目简介、运行步骤（占位）

### P0 PDF 拆页与基本信息读取
□ T09. 新建 boocr/pdf_utils.py
□ T10. 实现 PDF 拆页与光栅化为 ndarray
□ T11. 编写单元测试（读取示例 PDF，断言返回 PageImage 对象）

### P1 图像预处理
□ T12. 新建 boocr/image_proc.py
□ T13. 实现灰度化 + Otsu 二值化函数
□ T14. 实现可选手动倾斜校正（角度参数）
□ T15. 写对应单元测试（读取示例图，断言返回 ndarray shape）

### P2 列检测与裁切
□ T16. 新建 boocr/col_detect.py
□ T17. 实现垂直投影求列分割线（自动列数）
□ T18. 支持 CLI 覆盖列数参数（传入 pipeline）
□ T19. 输出 ColumnCrop 列表 + bbox；单元测试断言列数范围

### P3 竖排 OCR（繁体）
□ T20. 新建 boocr/ocr.py
□ T21. 集成 PaddleOCR vertical 模式，加载繁体模型
□ T22. 编写 PaddleOCR 模型下载脚本 / 缓存检测，首次运行自动处理
□ T23. 编写封装函数 `run_ocr(crop: ndarray) -> str`
□ T24. 在 tests/ 加入 1 个小图块 OCR 快速测试（跳过慢测）

### P4 繁→简体转换
□ T25. 新建 boocr/converter.py
□ T26. 使用 opencc-py 调用 "t2s.json" 转换；保持长度一致断言
□ T27. 单元测试：繁体字符串 → 简体字符串

### P5 竖排排版（简体文字 PDF）
□ T28. 新建 boocr/composer.py
□ T29. 使用 reportlab/fpdf2，根据 OCR 结果在对应位置绘制简体文字
□ T30. 保存 `page_simplified.pdf`，确保文字可搜索
□ T31. 单元测试：给定 OcrResult 列表生成 PDF 并断言文件可解析

### Pipeline 串联
□ T32. 在 boocr/pipeline.py 实现 run_pipeline(input_path, output_path) 调度 P0–P5
□ T33. 更新 boocr/cli.py 调用 pipeline 并打印 "DONE" + 0 返回码

### 集成与示例
□ T34. 准备 3 页示例 PDF 到 tests/assets/
□ T35. 编写 scripts/e2e.ps1：一键跑 `boocr poc --input <...>.pdf --output <...>.pdf` 并断言输出文件存在
□ T36. 在 docs/ 更新快速上手指南（CLI 示例）

### 质量与文档（核心）
□ T37. 完善技术设计文档章节 4–8 细节（依赖版本、数据流图）
□ T38. 初稿 PRD & 技术文档同步审阅自检

### ★ 可选任务（进度充裕时再做）
□ T39. 配置 pre-commit（black / isort / flake8）
□ T40. 设置 pytest 覆盖率阈值 ≥ 80%，输出报告
□ T41. 撰写 FAQ：Windows OpenCV/Paddle 安装问题
□ T42. 每日 push 并打 tag（D1…D4）；在 GitHub Releases 草稿附安装步骤
□ T43. 完成 D4 里程碑后整理 changelog
□ T44. 预研批处理与 GUI 需求，记录在 docs/todo_future.md
