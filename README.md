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

## 使用方法

```bash
boocr run --input <输入目录> --output <输出目录>
boocr resume --input <输入目录> --output <输出目录>
boocr version
``` 