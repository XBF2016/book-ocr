# 任务 #3：依赖锁定

## 任务描述
执行 `poetry lock` 并提交 `poetry.lock` 文件，锁定项目依赖版本，确保开发环境一致性。

## 前置检查
1. **Poetry 版本**
   - 执行 `poetry --version`，确保 ≥ 1.6
   - 若未安装或版本过旧，先升级：`pip install -U poetry`
   
2. **pyproject.toml 完整性**
   - 已在 `[tool.poetry.dependencies]`、`[tool.poetry.group.dev.dependencies]` 等区块声明运行时 / 开发依赖
   - 若之前只写了运行时依赖，本次不需改动；后续配置 pre-commit 时再补充 dev 依赖
   
3. **虚拟环境位置策略**
   - 可选：`poetry config virtualenvs.in-project true`，将 `.venv/` 放到项目根目录，便于隔离

## 执行步骤
1. **生成锁文件**
   ```bash
   poetry lock
   ```
   - 首次运行会解析 `pyproject.toml` 并写入 `poetry.lock`
   - 若依赖解析失败，按提示调整版本约束或添加源
   
2. **校验可安装性**
   ```bash
   poetry install --no-root
   ```
   - 确认所有依赖在当前平台可解析、编译通过
   
3. **Git 操作**
   ```bash
   git add poetry.lock
   git commit -m "chore: lock dependencies with poetry.lock (task #3)"
   ```
   - 若 `.gitignore` 排除了 `poetry.lock`，记得移除规则

## 文档同步
1. **更新 `docs/tasks.md`**
   - 将 3.「依赖锁定」状态改为 `√`
   - 将指针 `→` 移动到 4.「预提交钩子」
   
2. **可选：在 `README.md` 补充**
   在「快速开始」或「开发环境」小节补充一句：
   > `poetry install` 会自动读取 `poetry.lock` 以复现一致的依赖树。

## 验收标准
- `poetry.lock` 文件存在且已提交
- 全新 clone + `poetry install --no-root` 能成功创建一致的虚拟环境
- `docs/tasks.md` 状态与指针同步更新

## 可能的坑与对策
1. **Windows 下编译依赖失败**
   - 安装 VS Build Tools 或使用 `--all-extras` 的预编译轮子源
   
2. **私有/国内源加速**
   - 在 `poetry config repositories.*` 配置镜像，避免锁文件里混入不同 URL
   
3. **依赖冲突**
   - 使用 `poetry update <pkg>` 或放宽约束，直至 `poetry lock` 通过 