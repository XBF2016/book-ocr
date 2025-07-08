# 任务 #5：CI-lint GitHub Actions

## 一、工作目标
1. 在 GitHub Actions 上自动执行静态检查：
   * 代码风格 / 复杂度：ruff  
   * 类型检查：mypy  
2. 只在 **push / PR** 时运行，支持本地复用同一套配置。  
3. 运行速度快：使用缓存，控制依赖安装时间 < 30 s。  

## 二、文件与目录
1. `.github/workflows/ci-lint.yml` ← 新增  
2. `pyproject.toml`         ← 补充 mypy/ruff 配置（若本地已有可跳过）  
3. `docs/tasks.md`         ← 更新进度：#5 标记为 √，指针移动到 #6  

## 三、YAML 工作流示例
```yaml
name: CI – Lint

on:
  pull_request:
  push:
    branches: [master]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - name: ⬇️ Checkout
        uses: actions/checkout@v4

      - name: 🔧 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: ♻️ Cache Poetry
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-${{ runner.os }}-${{ hashFiles('poetry.lock') }}
          restore-keys: |
            poetry-${{ runner.os }}-

      - name: ♻️ Cache venv
        uses: actions/cache@v4
        with:
          path: ~/.venv
          key: venv-${{ runner.os }}-${{ hashFiles('poetry.lock') }}
          restore-keys: |
            venv-${{ runner.os }}-

      - name: 📦 Install dependencies
        run: |
          pip install poetry
          poetry config virtualenvs.in-project true
          poetry install --no-interaction --with dev

      - name: 🕵️ Ruff check
        run: poetry run ruff check .

      - name: 🕵️ Mypy type check
        run: poetry run mypy book_ocr tests
```

## 四、`pyproject.toml` 片段（如无则添加）

```toml
[tool.ruff]
line-length = 120
target-version = "py311"
exclude = ["tests/__init__.py"]

[tool.mypy]
python_version = "3.11"
strict = true
show_error_codes = true
ignore_missing_imports = true
```

## 五、更新任务清单 `docs/tasks.md`
* 把第 5 项前缀由 `→` 改为 `√`  
* 将指针 `→` 移到第 6 项【CI-test】  

## 六、提交信息模板
```
feat(ci): add GitHub Actions lint workflow (ruff + mypy)

- 新增 .github/workflows/ci-lint.yml
- 配置 ruff / mypy 到 pyproject.toml
- 更新 docs/tasks.md 进度指针
```

按以上步骤实施并推送后，CI 应自动触发并通过，从而完成任务 #5。 