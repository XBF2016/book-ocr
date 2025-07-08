# 【技术架构设计说明书】—「古籍竖排繁‧简对照生成工具」  
版本：v1.0 编写日期：YYYY-MM-DD 作者：XXX（技术架构师）

---

## 1. 目的
依据《MVP 需求说明书》v1.0，在 30 天内交付一款跨平台 CLI 工具，实现「扫描版竖排古籍 → 竖排繁简对照 PNG + 可全文检索 PDF」的完整闭环。本技术架构文档用于：

1. 明确系统边界与职责  
2. 规划可伸缩、可维护的模块化组件  
3. 指导后续研发、测试、部署与运维  

---

## 2. 技术选型

| 领域 | 方案 | 选型原因 |
|------|------|----------|
| 语言 | Python 3.11 | 图像/文本处理生态成熟，跨平台，社区活跃 |
| 打包 | PyInstaller / Nuitka | 生成单文件可执行；兼容 Win10 / Ubuntu |
| 深度学习框架 | PaddleOCR（竖排中文模型） | 内置方向分类、检测、识别；GPU 支持；准确率 & 性能均衡 |
| 图像处理 | OpenCV 4.x | 倾斜校正、二值化、形态学操作 |
| 繁→简 | OpenCC 1.1 | 转换质量高，MIT 协议 |
| PDF 处理 | PyMuPDF / fitz | 嵌入文本层、合并分页，GPU 无依赖 |
| CLI 框架 | Typer (基于 Click) | type hint 友好，自动生成 `--help` |
| 日志 | loguru | 彩色终端、文件旋转、跨模块统一 |
| 配置 | Pydantic + YAML | 强类型校验，支持环境变量覆写 |
| 测试 | pytest + hypothesis | 单元 & 属性测试 |
| CI/CD | GitHub Actions | 自动 lint/测试/打包；发布到 Release |
| 容器化 | Docker + NVIDIA CUDA 镜像 | 保证 GPU 环境一致性（可选） |
| 代码质量 | ruff + mypy + pre-commit | 自动格式化、静态类型检查、提交前质量把关 |

---

## 3. 总体架构

```
┌──────────────────────────────┐
│          CLI 层 (Typer)       │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│       Pipeline 调度层         │
│  - TaskManager (run/resume)  │
│  - PageWorker (并发控制)      │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│     图像/文本处理核心层        │
│  F1 Preprocessor             │
│  F2 ColumnDetector           │
│  F3 OCRRecognizer            │
│  F4 OpenCCConverter          │
│  F5 DualTypesetter           │
│  F6 Exporter (PNG/PDF)       │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│         基础支撑层             │
│  - ConfigService             │
│  - LoggingService            │
│  - MetadataStore (meta.json) │
│  - CheckpointStore (state)   │
└──────────────────────────────┘
```

1. **分层解耦**：CLI → 调度 → 业务核心 → 基础支撑  
2. **管道式处理**：每页按 F1~F6 顺序流经；支持页级并行  
3. **幂等与断点续跑**：CheckpointStore 记录已完成页索引；`resume` 仅处理缺失页  
4. **事件驱动日志**：核心层通过 LoggingService 统一输出，支持 DEBUG/INFO/ERROR 级别  
5. **可插拔**：OCR/排版模块预留策略接口，便于后续替换模型或算法  

---

## 4. 模块设计

### 4.1 CLI 层
```
boocr run    --input <dir> --output <dir> [--gpu] [--threads N] [--config cfg.yml]
boocr resume --input <dir> --output <dir>
boocr version
```
- 参数校验失败即刻返回非零码  
- 自动为输出目录添加时间戳子文件夹（可关闭）  

### 4.2 Pipeline 调度层
| 类 | 关键方法 | 说明 |
|----|----------|------|
| `TaskManager` | `run()`, `resume()` | 解析输入文件夹，生成页任务队列 |
| `PageWorker`  | `process(page_path)` | 线程池 / 进程池并发；GPU 只能单进程时退化为同步 |

### 4.3 核心处理层
1. **Preprocessor**  
   - OpenCV：自适应阈值二值化  
   - HoughLines + 仿射变换：倾斜校正（±5°）  
2. **ColumnDetector**  
   - Projection profile + 滑窗；返回列 bbox（误差 ≤1 字宽）  
   - 可选连通域分割兜底  
3. **OCRRecognizer**  
   - PaddleOCR 参数：`--rec_char_type=ch` `--layout=True`  
   - 竖排方向分类模型 on / off 自动切换  
4. **OpenCCConverter**  
   - `tw2sp.json` 词表，保证字符数一致  
5. **DualTypesetter**  
   - Pillow 画布：右繁/左简；20 px 间距；用户可通过 YAML 指定字体/字号  
6. **Exporter**  
   - `page_###_dual.png`  
   - `book.pdf`：PyMuPDF 按页插入 PNG，嵌入简体文本层（bbox 对齐）  
   - `meta.json`：存 OCR 字串、bbox、conf  

### 4.4 基础支撑层
- **ConfigService**：加载默认配置 → 合并用户 YAML → 环境变量覆写  
- **LoggingService**：`loguru` 彩色输出、`*.log` 日志旋转，保留 30 天  
- **MetadataStore**：实时写入/追加 `meta.jsonl`，结束后合并为最终 `meta.json`  
- **CheckpointStore**：JSON/SQLite 记录页状态（pending/done/failed）  

---

## 5. 数据模型

```python
class Column(BaseModel):
    index: int
    text_tra: str
    text_simp: str
    bbox: tuple[int, int, int, int]
    conf: float

class PageMeta(BaseModel):
    page: int
    columns: list[Column]

class Checkpoint(BaseModel):
    page: int
    status: Literal["pending", "done", "failed"]
    updated_at: datetime
```

---

## 6. 关键技术挑战 & 解决方案

| 挑战 | 方案 |
|------|------|
| 古籍竖排 OCR 罕见字 | 预留 `--custom_dict path` / 深度学习再训练接口 |
| 页边批注干扰列检测 | CLI 参数 `--margin-cut N`，预处理裁切 |
| GPU/CPU 环境差异 | 自动探测 CUDA；无 GPU 时降级到 CPU 并提示性能警告 |
| 断点续跑一致性 | Checkpoint 采用「先写 pending，完成改 done」事务式模式，防宕机丢失 |

---

## 7. 日志、监控与错误处理

1. **日志格式**：`[YYYY-MM-DD HH:MM:SS] [LEVEL] [page=###] message`  
2. **失败列表**：`failed.txt` 记录失败页路径，方便人工复现  
3. **性能指标**（--verbose）：每页处理耗时、OCR 置信度统计  
4. **监控集成**：预留 `--prometheus-port` 暴露 `/metrics`（可选）  

---

## 8. 性能与并发策略

| 目标 | 指标 | 策略 |
|------|------|------|
| 单页 ≤ 5 s | GTX 1060 | - GPU 批量推理 <br> - I/O 与推理流水并行 |
| 内存 ≤ 2 GB | 高分辨率 | - 分页读取 <br> - OCR 图块分批释放 |
| 吞吐 | N 张/批 | 线程池并行预处理；OCR 单进程 GPU；排版/导出回到多线程 |

---

## 9. 安全与合规
- 输入输出文件路径合法性校验（避免路径穿越）  
- 临时文件夹默认位于用户目录 `.boocr/tmp` 并定期清理  
- 遵循依赖库许可证（MIT、Apache 2.0、AGPL）并在 `NOTICE` 中列出  

---

## 10. 部署与交付

1. **本地二进制**  
   - `make build` → `/dist/boocr.exe|boocr`  
   - 发布到 GitHub Release，附 SHA256  
2. **Docker**（可选 GPU 版）  
   ```bash
   docker build -t boocr:gpu -f docker/Dockerfile.gpu .
   docker run --gpus all -v /raw:/in -v /out:/out boocr:gpu run -i /in -o /out
   ```  
3. **版本策略**：`MAJOR.MINOR.PATCH`，MVP 首发 `1.0.0`  

---

## 11. 代码组织

```
book_ocr/
  boocr/                # 源码包
    cli.py              # Typer 入口
    pipeline/           # 调度
    modules/            # 核心 F1~F6
    services/           # 基础支撑
    models/             # Pydantic 数据模型
    utils/
  tests/
  docker/
  scripts/
```

---

## 12. 质量保证

- **静态检查**：ruff + mypy  
- **单元测试覆盖率** ≥ 80%（核心逻辑）  
- **集成测试**：CI 触发，随机取 3 页公开古籍样本，校验产物哈希  
- **性能基准**：pytest-benchmark 保存基线，回归触发告警  
- **代码质量工具**：
  - **pre-commit**：Git提交前自动执行代码质量检查
  - **ruff**：统一的Python linter，自动格式化与代码规范检查
  - **mypy**：静态类型检查器，减少类型相关错误
  - **pytest**：单元测试框架，确保功能正确性

### 12.1 开发流程与工具链

开发者遵循以下流程确保代码质量：

1. **本地开发环境搭建**
   ```bash
   # 安装依赖
   poetry install
   
   # 激活pre-commit钩子
   poetry run pre-commit install
   ```

2. **提交前自动检查**
   - Git commit触发pre-commit钩子
   - 运行ruff格式化与规范检查
   - 执行mypy类型检查
   - 运行快速单元测试
   
3. **持续集成流程**
   - GitHub Actions自动执行更全面的测试
   - 分支合并需要通过CI检查
   - 定期运行性能基准测试

4. **代码审核标准**
   - 100% 通过 ruff 与 mypy 检查
   - 无未解决的 TODO 或 FIXME 标记
   - 关键功能有单元测试覆盖

---

## 13. 里程碑对齐

| 里程碑 | 架构交付物 | 验证方式 |
|--------|-----------|---------|
| M1 | Preprocessor、ColumnDetector 原型 | 单元 & 视觉 diff |
| M2 | OCRRecognizer、Converter、日志 | 抽样准确率 > 85% |
| M3 | Typesetter、Exporter、Checkpoint | 生成示例 PDF |
| M4 | 全链路测试、优化、文档 | 验收测试通过 |

---

## 14. 风险与对策（补充）

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| OCR 模型更新导致推理接口变动 | 中 | 抽象 `OCRBackend` 适配层 |
| 高 DPI 图像超内存 | 中 | 分块裁切，临时文件落盘 |
| Windows 字体缺失导致排版错位 | 低 | 工程包内置宋体/楷体开源字体 |

---

## 15. 结语
本技术架构文档详细阐述了「古籍竖排繁简对照生成工具」在 MVP 阶段的整体技术方案、模块划分、关键流程与风险控制，为团队研发提供清晰的蓝图。后续若需求或环境发生变化，应按照本架构的扩展点进行迭代，确保系统持续稳定、高效地服务于录校员与研究者。 