# 古籍竖排繁‧简对照生成工具 - 任务清单

→ 下一个任务：T01  
提示：做完一个任务记得 **更新任务状态（√/□）和指针**  

## 任务清单  
（√＝已完成，□＝未完成）

### 基础准备  
□ T01. 初始化本地 git 仓库：clone、创建 poc 分支，提交初始 README  
□ T02. 创建 virtualenv 并写入 requirements.txt（Python 3.11 / click / numpy / Pillow / OpenCV / opencc-py / paddleocr 等）  

### 目录与骨架  
□ T04. 在 tests/ 添加 pytest 初始化与示例占位文件  
□ T05. 新建 boocr/ 包及空 __init__.py  
□ T06. 创建 boocr/cli.py：click 入口 `boocr poc --input <img> --output <dir>` 雏形（打印 "TODO"）  
□ T07. 创建 boocr/pipeline.py：定义同步串行调用接口（空实现）  
□ T08. 在 boocr/dataclasses.py 定义 PageImage / ColumnCrop / OcrResult / DualText / RenderConfig  
□ T09. 更新 README：项目简介、运行步骤（占位）  

### P1 图像预处理  
□ T10. 新建 boocr/image_proc.py  
□ T11. 实现灰度化 + Otsu 二值化函数  
□ T12. 实现可选手动倾斜校正（角度参数）  
□ T13. 写对应单元测试（读取示例图，断言返回 ndarray shape）  

### P2 列检测与裁切  
□ T14. 新建 boocr/col_detect.py  
□ T15. 实现垂直投影求列分割线（自动列数）  
□ T16. 支持 CLI 覆盖列数参数（传入 pipeline）  
□ T17. 输出 ColumnCrop 列表 + bbox；单元测试断言列数范围  

### P3 竖排 OCR（繁体）  
□ T18. 新建 boocr/ocr.py  
□ T19. 集成 PaddleOCR vertical 模式，加载繁体模型  
□ T41. 编写 PaddleOCR 模型下载脚本 / 缓存检测，首次运行自动处理  
□ T20. 编写封装函数 `run_ocr(crop: ndarray) -> str`  
□ T21. 在 tests/ 加入 1 个小图块 OCR 快速测试（跳过慢测）  

### P4 繁→简体转换  
□ T22. 新建 boocr/converter.py  
□ T23. 使用 opencc-py 调用 "t2s.json" 转换；保持长度一致断言  
□ T24. 单元测试：繁体字符串 → 简体字符串  

### P5 双列排版渲染  
□ T25. 新建 boocr/renderer.py  
□ T26. 实现 Pillow 逐行渲染右繁左简，固定列间距 20 px  
□ T27. 保存 `page_dual.png`，分辨率与输入一致  
□ T28. 单元测试：给定 DualText 列表生成图片并断言文件尺寸  

### Pipeline 串联  
□ T29. 在 boocr/pipeline.py 实现 run_pipeline(input_path, output_dir) 调度 P1–P5  
□ T30. 更新 boocr/cli.py 调用 pipeline 并打印 "DONE" + 0 返回码  

### 集成与示例  
□ T31. 准备 3 页示例图到 tests/assets/  
□ T32. 编写 scripts/e2e.ps1：一键跑 `boocr poc` 并断言输出文件存在  
□ T33. 在 docs/ 更新快速上手指南（CLI 示例）  

### 质量与文档（核心）  
□ T35. 完善技术设计文档章节 4–8 细节（依赖版本、数据流图）  
□ T37. 初稿 PRD & 技术文档同步审阅自检  

### ★ 可选任务（进度充裕时再做）  
□ T03. 配置 pre-commit（black / isort / flake8）  
□ T34. 设置 pytest 覆盖率阈值 ≥ 80%，输出报告  
□ T36. 撰写 FAQ：Windows OpenCV/Paddle 安装问题  
□ T38. 每日 push 并打 tag（D1…D4）；在 GitHub Releases 草稿附安装步骤  
□ T39. 完成 D4 里程碑后整理 changelog  
□ T40. 预研批处理与 GUI 需求，记录在 docs/todo_future.md 