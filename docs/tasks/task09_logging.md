# 任务 #9 - Logging-核心

## 设计目标  
1. 项目内任何模块都能通过 `from book_ocr.logger import get_logger` 取得同一个日志实例。  
2. 支持在 CLI 启动时一次性完成日志级别与输出位置配置；库模式调用时也能自动获得一个合理的默认配置。  
3. 兼容标准 `logging`（第三方库若使用 `logging.getLogger` ，日志同样流向 Loguru）。  
4. 代码零侵入：业务层面只关心 `logger.debug/info/warning/error`。  

## 落地方案  
### 1. 依赖声明  
pyproject.toml 中添加：
```toml
[tool.poetry.dependencies]
loguru = "^0.7"
```  

### 2. 新增文件结构  
```
book_ocr/
  ├─ logger.py        # 对外暴露 get_logger
  └─ _logging_core.py # 内部：真正封装 Loguru
tests/
  └─ test_logger.py   # 单元测试
```  

### 3. 模块实现要点  
#### _logging_core.py  
- 私有函数 `_bootstrap()`：  
  * 检测环境变量 `BOOCR_LOG_LEVEL`，否则默认 `INFO`。  
  * 先移除 Loguru 默认 sink，再添加一个 `stderr` 彩色输出 sink。  
- 公共函数 `configure(**kwargs)`：供 CLI 手动覆写（#10 将在此添加文件轮转参数）。  
- 调用 `logging.Logger` → Loguru 的接管：  
  ```python
  import logging
  from loguru import logger
  class InterceptHandler(logging.Handler):
      def emit(self, record):  # 此处做 level、文件名映射
          try:
              level = logger.level(record.levelname).name
          except ValueError:
              level = record.levelno
          logger.bind(module=record.name).log(level, record.getMessage())
  logging.basicConfig(handlers=[InterceptHandler()], level=0)
  ```  

#### logger.py  
```python
from ._logging_core import _bootstrap
from loguru import logger as _root_logger

_bootstrap()     # 在首次 import 时完成默认配置

def get_logger(name: str | None = None):
    """获取带 name 的 logger；name 为 None 时返回根 logger"""
    return _root_logger if name is None else _root_logger.bind(module=name)
```  

### 4. CLI 层对接（提前铺路）  
- `cli.py` 顶部先 `from book_ocr.logger import get_logger`, 并在 `app.callback()` 中添加 `--log-level` 选项；收到参数后调用 `configure(level=xxx)`。  
- 若 CLI 未显式传参，默认配置已在 `_bootstrap()` 完成。  

### 5. 单元测试 tests/test_logger.py  
1. `test_singleton()`：多次 `get_logger()` 对比 `id()` 相同。  
2. `test_intercept_std_logging(capsys)`：  
   ```python
   import logging
   from book_ocr.logger import get_logger
   std_logger = logging.getLogger("std")
   std_logger.warning("hello")
   captured = capsys.readouterr().err
   assert "hello" in captured and "std" in captured
   ```  
3. `test_bind_name(capsys)`：`get_logger("abc").info("msg")` 输出应含 `abc`。  

### 6. 文档  
- 在当前文档（docs/tasks/task09_logging.md）写明使用示例、环境变量、CLI 参数说明。  

### 7. Git 提交流程  
1. `feat(logging/core): add loguru wrapper & get_logger`  
2. 更新 `docs/tasks.md`：将 #9 标记为 √，指针移至 #10。  
3. Push & 确保 CI 通过。  

## 使用示例

```python
# 在任何模块中获取日志记录器
from book_ocr.logger import get_logger

# 默认 logger
logger = get_logger()
logger.info("这是一条普通日志")
logger.error("发生错误")

# 带模块名的 logger
page_logger = get_logger("page_processor")
page_logger.debug("处理第 1 页")
```

## 环境变量说明
- `BOOCR_LOG_LEVEL`: 设置日志级别，可选值 `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`，默认为 `INFO`。

## CLI 参数说明
- `--log-level`: 命令行参数，用于覆盖环境变量设置的日志级别。 