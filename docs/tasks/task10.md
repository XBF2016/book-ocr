# 任务 #10：Logging-旋转

## 任务描述
实现日志按日旋转功能与最大文件数配置。

## 需求拆解  
1. 支持按日自动滚动日志文件（rotation="00:00"）。  
2. 支持限制本地最多保留 N 个日志文件（retention=N 或自定义函数）。  
3. 保持现有 stderr 彩色输出不变。  
4. 默认行为即可满足大多数场景；CLI／环境变量／YAML 后续配置任务再覆盖。  
5. 单元测试覆盖：  
   • 生成日志 > 24 h 后文件名变更；  
   • 超出保留数量后旧文件被删除。  

## 设计要点  
1. 日志目录  
   • 默认 `logs/`（若不存在自动创建）。  
   • 文件名模板：`boocr_{time:YYYY-MM-DD}.log`。  

2. Sink 规划  
   • console sink：已有，继续彩色输出。  
   • file sink：`logger.add(path, rotation="00:00", retention=max_files, encoding="utf-8")`。  
   • 建议在 `_bootstrap()` 中就添加 file sink，使所有模块都写入。  

3. 配置入口  
   • `_bootstrap()` 读取两环境变量：  
     - `BOOCR_LOG_DIR`（可选）；  
     - `BOOCR_LOG_MAX_FILES`（默认为 7）。  
   • `configure(**kwargs)` 保留向后兼容，若用户想改动 rotation/retention，可通过该函数注入额外参数。  

## 实施步骤  
1. 修改 `book_ocr/_logging_core.py`  
   • 创建日志目录；  
   • 读取 env；  
   • `logger.add(file_path, rotation="00:00", retention=int(max_files), ...)`。  

2. 补充单元测试  
   • 在 `tests/test_logger.py`：  
     - 使用 `tmp_path` 创建临时 logs 目录；  
     - 打两条日志 → 手动移动时间戳(或模拟 rotation 函数) → 断言生成第二个文件；  
     - 写入 N+1 天的日志 → 断言仅保留 N 个文件。  

3. 更新文档  
   • `docs/tasks.md`：将任务 #10 状态改为 √ 并把"→"指向 #11；  
   • 在 `docs/task09_logging.md` 或新建 `task10.md` 说明 rotation 与 retention 的环境变量用法。  

4. Git 操作  
   • 每个子步骤完成后提交：  
     - feat(logging): daily rotation & retention  
     - test(logging): add rotation/retention tests  
     - docs(logging): usage for env vars  

## 注意事项  
• loguru 的 `retention` 既支持整数也支持回调；若日后需要更复杂策略，可把数字转函数封装。  
• Windows 上路径分隔符与编码问题，统一使用 `pathlib.Path` 并显式 `encoding="utf-8"`。  
• 先跑 `pytest -q`; 通过 CI 后再合并。 