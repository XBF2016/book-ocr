# 任务 #7【CI-build】GitHub Actions step：PyInstaller 打包产物

## 【一】任务目标  
1. 在 GitHub Actions 中新增「Build」工作流。  
2. 触发条件：push / pull_request 到 master 分支 & tag（用于后续 Release）。  
3. 环境：Ubuntu 最新版镜像。  
4. 步骤：  
   - Checkout → 缓存 Poetry & pip → 安装依赖  
   - 运行 pytest（确保测试仍通过）  
   - 执行 PyInstaller 打包（单文件或 dist 目录均可）  
   - 上传构建产物到 workflow run（`actions/upload-artifact`）  
5. 产物：  
   - `boocr` 可执行文件（Linux 下无扩展名）  
   - 可选：生成 zip/tar.gz，以便后续 Release 直接复用  
6. 通过后，将 `docs/tasks.md` 中「→ 指针」移动到任务 #8。

## 【二】实现步骤  
1. 在仓库根新建 `.github/workflows/ci-build.yml`（或沿用你已创建的 `ci-test.yml` 命名规范，保持一致）。  
2. 复用现有安装脚本  
   - 你在 `ci-test` 中应已写好「设置 Python + 缓存 Poetry」段落，可直接 `copy & adjust`。  
3. 加入 PyInstaller  
   - Poetry 添加开发依赖：`poetry add --group dev pyinstaller`  
   - 打包命令示例：  
     ```bash
     poetry run pyinstaller -y \
       --name boocr \
       --onefile \
       --console \
       book_ocr/cli.py
     ```  
   - 打包后产物位于 `dist/boocr`。  
4. 上传 Artifact  
   ```yaml
   - name: Upload binary
     uses: actions/upload-artifact@v4
     with:
       name: boocr-linux
       path: dist/boocr
       retention-days: 14
   ```  
5. （可选）多平台矩阵  
   - 若短期仅需 Linux，可先实现单平台，后续再扩展。  
   - 多平台时 Windows 要处理 `.exe`；macOS 要注意签名。  
6. 更新任务清单  
   - 将任务 7 标记为 √  
   - 移动「→ 指针」到任务 8  
   - 将 `.github/workflows/ci-build.yml` 加入版本控制并提交。

## 【三】ci-build.yml 参考骨架  
```yaml
name: Build
on:
  push:
    branches: [master]
    tags: ['v*']
  pull_request:
    branches: [master]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # ==== 缓存 Poetry ====
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'poetry'

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: poetry install --no-interaction --no-ansi

      # ==== 运行测试 ====
      - name: Run tests
        run: poetry run pytest -q

      # ==== 打包 ====
      - name: Build binary
        run: poetry run pyinstaller -y --name boocr --onefile --console book_ocr/cli.py

      # ==== 上传产物 ====
      - name: Upload binary artifact
        uses: actions/upload-artifact@v4
        with:
          name: boocr-linux
          path: dist/boocr
```

## 【四】后续检查清单  
- [ ] 本地执行 `poetry run pyinstaller ...` 可产生成功并运行 `./dist/boocr --help`。  
- [ ] GitHub Actions run 成功，无错误 & Artifact 可下载。  
- [ ] 更新 `README.md`：添加「构建状态 badge」及简要使用示例（可等待任务 #63 一并处理）。  
- [ ] `docs/tasks.md` 状态同步。 