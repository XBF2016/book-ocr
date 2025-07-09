# 任务 #6：CI-test

## 目标拆解  
1. 在现有 CI（已跑 ruff + mypy）基础上，新增 pytest 步骤，保证单元测试通过，失败即中断工作流。  
2. 启用依赖缓存，降低 Poetry 安装时间与 pytest 收集缓存开销。  
3. 运行结果（测试数、耗时）输出到日志；如有需要，可上传 coverage 或测试报告后续再做。  

## 实施步骤  
1. 工作流文件定位  
   - 路径：`.github/workflows/ci.yml`（或现有文件名），在现有 job 末尾插入/追加步骤。  
   - 如果 ruff+mypy 已在 job `lint`，可以将测试放入同一个 job，也可以拆分新 job `test`；建议拆分，以便并行并使用独立缓存。  

2. 复用／新增 Action  
   a. `actions/setup-python`：指定 3.11（或 `{{ matrix.python-version }}`）。  
   b. `actions/cache`：  
      - key：`poetry-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}`  
      - path：`~/.cache/pypoetry` 及 `~/.cache/pip`（Poetry install 时用到）。  
   c. `snok/install-poetry`（或官方指令）安装 Poetry 指定版本。  

3. Job `test` 参考示例  
   ```yaml
   test:
     needs: lint          # 如果依赖 lint 通过才测
     runs-on: ubuntu-latest
     strategy:
       matrix:
         python-version: ["3.10", "3.11"]
     steps:
       - uses: actions/checkout@v4

       - uses: actions/setup-python@v5
         with:
           python-version: ${{ matrix.python-version }}

       - uses: actions/cache@v4
         with:
           path: |
             ~/.cache/pypoetry
             ~/.cache/pip
           key: poetry-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}

       - uses: snok/install-poetry@v1
         with:
           virtualenvs-create: true
           virtualenvs-in-project: true

       - name: Install dependencies
         run: poetry install --no-interaction --no-root

       - name: Run pytest
         run: poetry run pytest -q
   ```
   说明：  
   - `-q` 安静模式，失败自动抛非零状态终止。  
   - 若后续要加 coverage，可改为 `pytest --cov=book_ocr --cov-report=xml` 并 `actions/upload-artifact` 上传。  

4. 本地验证  
   - 在本地执行 `poetry run pytest`，确认所有测试通过（当前仅 `tests/test_cli.py`，运行时间极短）。  
   - `act` 工具可模拟 GitHub Actions；或直接推送分支触发 CI 观察执行耗时与缓存命中情况。  

## 交付物与检查点  
1. `.github/workflows/ci.yml` 更新（新增 job `test`）。  
2. README 或 docs 中更新 CI Badge（后续与 build/release 一并处理）。  
3. 推送后确认：  
   - 两个 job 均通过。  
   - 第二次推送开始缓存命中，PyPI 依赖安装耗时明显下降。 