# 任务 #4【预提交钩子】配置 pre-commit（ruff、mypy、pytest）

## 一、目标  
1. 在本地提交代码时自动执行代码质量检查，防止低级错误进入仓库。  
2. 工具链：pre-commit + ruff（格式 & lint）+ mypy（静态类型检查）+ pytest（快速回归测试）。  
3. 保证所有开发者零配置即可获得同样的提交前体验。

## 二、产出物  
1. `.pre-commit-config.yaml` – pre-commit 主配置文件  
2. `pyproject.toml` – ruff、mypy、pytest 相关配置补充（如已有可跳过）  
3. `docs/tasks.md` – 更新状态标记与指针  
4. `README.md` / `docs/technical_architecture.md` – 追加「开发环境搭建」段落（可合并到后续 CI 任务里完成）

## 三、实施步骤  
1. 安装基础工具  
   ```bash
   poetry add --group dev pre-commit ruff mypy pytest
   # 若已有 pytest / ruff，可省略
   ```

2. 编写 `.pre-commit-config.yaml`  
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.4.4         # 与 pyproject.toml 保持一致
       hooks:
         - id: ruff
           args: [--fix]   # 自动修复格式

     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.10.0
       hooks:
         - id: mypy
           args:
             - --strict
             - --pretty
           additional_dependencies: []  # 需要的第三方 stubs 可在此列举

     - repo: local
       hooks:
         - id: pytest
           name: pytest (fast)
           entry: pytest
           language: system
           types: [python]
           pass_filenames: false    # 跑全部测试
           args: [-q, -Werror]      # 静默输出 & 把警告视作错误
   ```

3. 配置 ruff & mypy  
   在 `pyproject.toml` 增加（或确认已有）：
   ```toml
   [tool.ruff]
   line-length = 120
   extend-select = ["I"]   # isort
   fix = true

   [tool.mypy]
   python_version = "3.11"
   strict = true
   ignore_missing_imports = true
   ```

4. 激活 pre-commit  
   ```bash
   pre-commit install
   # 可选：首次检查
   pre-commit run --all-files
   ```

5. 本地验证  
   - 随便修改一个 Python 文件，引入未格式化代码或类型错误再尝试 `git commit`，确保钩子拦截。  
   - 刻意让 pytest 失败，验证能阻止提交。  
   - Windows + Linux/Mac 各测试一次，保证 shebang / 换行符兼容。

6. 更新任务清单  
   - 将任务 #4 前缀由「→」改为「√」。  
   - 将「→」指针移动到任务 #5【CI-lint】。

## 四、时间预估  
- 开发与调试：1 h  
- 跨平台验证：0.5 h  
- 文档更新 & PR 评审：0.5 h  
合计：≈ 2 h

## 五、后续衔接  
1. 任务 #5【CI-lint】可直接复用本地 ruff/mypy 配置。  
2. 任务 #6【CI-test】可沿用 pytest 钩子参数。  
3. 若想加速钩子执行，可在 `.pre-commit-config.yaml` 里为 pytest 设置 `files: ^tests/.*_fast\.py$`，专跑轻量测试；重量级测试留给 CI。 