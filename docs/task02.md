# 任务 #2: 依赖声明 - 实施规划

## 一、范围界定
1. 覆盖后续任务清单里会用到的「运行时依赖」即可；开发、测试、类型检查等工具将放在 dev-extras。
2. 以 *CPython 3.10* 为最低版本（Windows 与 PyInstaller 友好），GPU 相关留给 extras（如 `paddlepaddle-gpu`）。
3. 采用 Poetry 「Caret (`^`) + 次要版本锁定」策略：  
   例如 `opencv-python>=4.8,<5` → `^4.8`，既保证兼容，也便于后期升级。

## 二、依赖分组与库选择
• Core（核心功能）
  - `typer`：CLI 框架
  - `pydantic`：数据模型与配置校验
  - `pyyaml`：YAML 解析
  - `loguru`：日志
  - `Pillow`：图像处理
  - `opencv-python`：二值化、去倾斜、投影分列
  - `paddleocr`：OCR 推理（CPU 版）
  - `opencc-python-reimplemented`：繁简转换
  - `PyMuPDF` (`fitz`)：PDF 读写与嵌入文本
  - `tqdm`：进度条（或 rich，但后者较重）

• Extras
  - `gpu`：`paddlepaddle-gpu`（根据 CUDA 版本再细分标签）
  - `pdf`：若需更强 PDF 操作，可加入 `pypdf` / `pdfplumber`
  - `dev`：ruff、mypy、pytest、pytest-benchmark、pre-commit 等

## 三、执行步骤
1. 初始化 Python 版本：
   ```bash
   poetry env use 3.10
   ```
2. 在 `pyproject.toml` 的 `[tool.poetry.dependencies]` 填入上表 core 包；`[tool.poetry.extras]` 定义 `gpu`、`dev` 等组。
3. 先 **不** 执行 `poetry install`，待任务 #3「依赖锁定」再一次性生成 `poetry.lock`，保证锁文件可审阅。
4. 补充 `[build-system]`、`[tool.ruff]`、`[tool.mypy]` 的空节，方便后续任务 (#4 预提交钩子、#5~#6 CI-Lint/Test) 直接追加配置。
5. 手动跑一遍 `poetry export -f requirements.txt --without-hashes`，确认没有冲突。
6. 更新任务标记：
   - 在 `docs/tasks.md` 中将任务 #2【依赖声明】从 ▶ 改为 √ (已完成)
   - 将任务 #3【依赖锁定】从 □ 改为 ▶ (当前进行中)
   - 将任务 #4【预提交钩子】从 □ 改为 → (下一任务)
   - 更新底部的进度指针：
     ```
     ## 当前进度指针
     - ▶ = 任务 #3【依赖锁定】
     - → = 任务 #4【预提交钩子】
     ```
7. Push / PR：提交 `pyproject.toml` 和更新后的 `docs/tasks.md`。

## 四、里程碑与风险
• 里程碑  
  1) pyproject.toml 通过审阅并合入  
  2) poetry.lock 生成且 CI 能成功安装依赖  

• 潜在风险  
  - Windows + PaddleOCR 依赖轮子可能较大，需分 GPU/CPU 包。  
  - `opencv-python` 与 `pillow` 在 PyInstaller 打包时体积较大，可后期通过 `opencv-python-headless` 精简。

## 五、下一步行动
A. 立即编辑 `pyproject.toml` 并写入核心依赖（不跑 install）。  
B. 提交 PR / 更新任务清单状态。  
C. 进入下一任务 #3「依赖锁定」：执行 `poetry lock`、生成 lock 文件并提交。 