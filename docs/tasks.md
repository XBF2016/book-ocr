# 古籍竖排繁简对照生成工具 - 编码任务清单

## 标记说明
- □ = 待开始
- → = 下一任务
- √ = 已完成

## 当前进度指针
- → = 任务 #8【CI-release】

**提示：** 完成任一任务后，务必更新本清单中的状态标记和「 → 指针」，保持最新进度。

## 基础框架
1. √【项目骨架】生成 `book_ocr/` 目录 & `pyproject.toml`  
2. √【依赖声明】在 `pyproject.toml` 写入运行时依赖  
3. √【依赖锁定】执行 `poetry lock` & 提交 `poetry.lock`  
4. √【预提交钩子】配置 pre-commit（ruff、mypy、pytest）

## CI / CD
5. √【CI-lint】GitHub Actions step：ruff + mypy  
6. √【CI-test】GitHub Actions step：pytest（含缓存）  
7. √【CI-build】GitHub Actions step：PyInstaller 打包产物  
8. □【CI-release】发布 Release 并上传二进制

## 日志服务
9. □【Logging-核心】封装 loguru：统一 logger 获取  
10. □【Logging-旋转】实现按日旋转 & 最大文件数配置  
11. □【Logging-格式】测试彩色终端 + 文件格式正确

## 配置服务
12. □【Config-默认】加载内置 YAML `default.yml`  
13. □【Config-合并】实现用户 YAML 覆盖逻辑  
14. □【Config-Env】实现环境变量覆写 (`BOOCR__x__y` 样式)  
15. □【Config-验证】单测：非法字段抛 `ValidationError`

## 数据模型
16. □【Model-Column】Pydantic `Column`  
17. □【Model-PageMeta】Pydantic `PageMeta`（含 list[Column]）  
18. □【Model-Checkpoint】枚举状态 + 时间戳字段  
19. □【Model-测试】三模型字段校验单元测试

## 持久化存储
20. □【Metadata-append】按页写入 `meta.jsonl`  
21. □【Metadata-merge】结束时合并为 `meta.json`  
22. □【Checkpoint-init】创建文件并写入 pending  
23. □【Checkpoint-update】状态迁移 pending→done/failed  
24. □【Checkpoint-atomic】单测：宕机模拟仍数据一致

## CLI 层
25. □【CLI-入口】`boocr` Typer 应用创建  
26. □【CLI-version】实现 `--version` 输出  
27. □【CLI-run 参数】`--input --output --gpu --threads --config`  
28. □【CLI-resume 参数】`--input --output`  
29. □【CLI-校验单测】非法路径 / 重复输出目录检测

## Pipeline 调度
30. □【TaskMgr-扫描】扫描目录→页列表  
31. □【TaskMgr-队列】页任务 FIFO / 可迭代  
32. □【Worker-线程池】CPU 线程池预处理  
33. □【Worker-GPU 互斥】GPU 单进程锁实现  
34. □【Worker-测试】模拟 5 页并行，顺序正确

## 图像处理核心层 (F1-F3)
35. □【Pre-binarize】自适应阈值函数  
36. □【Pre-deskew】HoughLines ±5° 矫正  
37. □【Pre-pipeline 单测】输入样图→输出直立二值图
38. □【ColDet-proj】垂直投影找谷值  
39. □【ColDet-滑窗】误差修正 ≤1 字宽  
40. □【ColDet-测试】人工标注 bbox 误差断言
41. □【OCR-backend】封装 PaddleOCR 加载与释放  
42. □【OCR-vertical】开启竖排方向识别开关  
43. □【OCR-infer 批量】列图批量推理接口  
44. □【OCR-测试】4 行样本字符正确率 ≥80%

## 文本处理与排版 (F4-F6)
45. □【OpenCC-wrapper】单函数转换 + 长度一致校验  
46. □【OpenCC-测试】繁简对列表驱动测试
47. □【Type-canvas】创建 Pillow 画布大小计算  
48. □【Type-render-TRA】绘制繁体列  
49. □【Type-render-SIM】绘制简体列 & 间距控制
50. □【PNG-save】输出 `page_###_dual.png`  
51. □【PDF-insert PNG】按页插入图片  
52. □【PDF-embed text】嵌入简体文本层 bbox 对齐  
53. □【Export-测试】PDF 可搜索 + 图片存在

## Pipeline 集成
54. □【Pipe-串联】TaskManager 依序调用 F1~F6  
55. □【Pipe-断点】接入 CheckpointStore，支持 resume  
56. □【Pipe-失败写】失败页写入 `failed.txt`  
57. □【Pipe-集成测】三页完整流程哈希校验

## 测试与性能
58. □【pytest-fixtures】共享测试资源、样本图像  
59. □【benchmark-基线】添加 pytest-benchmark & 5 s 断言

## 交付与部署
60. □【Build-script】`scripts/build.py` 调 PyInstaller  
61. □【Docker-GPU】编写 `docker/Dockerfile.gpu`  
62. □【Docker-测试】运行样例命令行通过  
63. □【README】安装 / 使用 / badge / 目录结构
