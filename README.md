# 古籍竖排繁简对照生成工具

将扫描版竖排古籍转换为竖排繁简对照的PNG和可搜索PDF。

## 功能

- 自动处理竖排古籍图像
- 生成繁体和简体对照排版
- 输出可搜索的PDF格式

## 安装

```bash
# 通过 pip 安装
pip install book-ocr

# 通过 poetry 安装（推荐开发者使用）
poetry install
```

poetry install 会自动读取 `poetry.lock` 以复现一致的依赖树。

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/your-username/book-ocr.git
cd book-ocr

# 安装依赖
poetry install

# 激活pre-commit钩子
poetry run pre-commit install

# 手动运行全部检查（可选）
poetry run pre-commit run --all-files
```

项目使用以下代码质量工具：
- **ruff**: 代码格式化与lint检查
- **mypy**: 静态类型检查
- **pytest**: 单元测试

## 使用方法

```bash
boocr run --input <输入目录> --output <输出目录>
boocr resume --input <输入目录> --output <输出目录>
boocr version
``` 