# 任务 #1【项目骨架】生成 `book_ocr/` 目录 & `pyproject.toml`

## 一、前置假设  
1. 已安装 Python 3.11（与技术架构保持一致）。  
2. 使用 Poetry 作为包管理／构建工具。  
3. 当前工作目录位于仓库根 `/book-ocr`。

## 二、步骤拆分  
1. 初始化 Poetry 项目  
   ```bash
   poetry init --name book-ocr -n
   # -n 跳过交互，稍后手动编辑 pyproject.toml
   ```
2. 创建源码顶级包  
   ```bash
   mkdir -p book_ocr/{pipeline,modules,services,models,utils}
   touch book_ocr/__init__.py
   ```
3. 创建 CLI 入口文件  
   ```bash
   touch book_ocr/cli.py
   ```
   - 先写一个极简 Typer 应用骨架，占个位：
     ```python
     import typer
     app = typer.Typer()

     @app.command()
     def version():
         """Print package version."""
         import importlib.metadata as importlib_metadata
         typer.echo(importlib_metadata.version("book-ocr"))

     if __name__ == "__main__":
         app()  # pragma: no cover
     ```

4. 编辑 `pyproject.toml` 关键字段  
   - `[tool.poetry]`  
     ```
     name = "book-ocr"
     version = "0.1.0"
     description = "古籍竖排繁简对照生成工具"
     authors = ["YOUR_NAME <you@example.com>"]
     readme = "README.md"
     packages = [{ include = "book_ocr" }]
     ```
   - `[tool.poetry.dependencies]`
     只保留 Python 版本，运行时依赖放在任务 #2 处理：  
     ```
     python = "^3.11"
     ```
   - `[tool.poetry.scripts]`  
     ```
     boocr = "book_ocr.cli:app"
     ```
5. 初始化 Git 跟踪并提交  
   ```bash
   git add pyproject.toml book_ocr
   git commit -m "chore: scaffold project skeleton & pyproject"
   ```

## 三、质量检查（可选）  
- `poetry check` 验证 `pyproject.toml` 语法。  
- `poetry run python -m book_ocr.cli version` 预期输出 `0.1.0`。

## 四、完成标记  
- 将 `tasks.md` 中  
  ```
  1. ▶【项目骨架】生成 ...
  ```  
  改为  
  ```
  1. √【项目骨架】生成 ...
  ```  
- 同时把 ▶ 指向任务 #2「依赖声明」。

## 五、下一步预告  
任务 #2 需要把运行时依赖（Typer、loguru、pydantic、opencv-python、paddleocr 等）写入 `[tool.poetry.dependencies]`，并再次提交。 