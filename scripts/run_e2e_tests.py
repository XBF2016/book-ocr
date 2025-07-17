#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集中测试脚本，整合了单元测试、端到端测试和覆盖率报告生成。
"""

import subprocess
import sys
from pathlib import Path
import os
import pdfplumber
import difflib

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.resolve()
VENV_PYTHON = ROOT_DIR / "venv-py311" / "Scripts" / "python.exe"
E2E_OUTPUT_PDF = ROOT_DIR / "output" / "e2e_test_result.pdf"
# 期望的简体文字基线文件
EXPECTED_TEXT_FILE = ROOT_DIR / "tests" / "assets" / "expected_simplified.txt"

def run_command(command, cwd=ROOT_DIR):
    """封装 subprocess.run，方便调用和调试"""
    print(f"Running command: {' '.join(command)}")
    try:
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Command not found - {command[0]}", file=sys.stderr)
        print("Please ensure the required tools are installed and in your PATH.", file=sys.stderr)
        return False


def run_unit_tests():
    """步骤 1：运行所有 pytest 单元测试"""
    print("\n--- 步骤 1: 运行单元测试 ---")
    command = [str(VENV_PYTHON), "-m", "pytest"]
    if not run_command(command):
        print("单元测试失败，测试终止。", file=sys.stderr)
        sys.exit(1)
    print("--- 单元测试通过 ---")
    return True


def run_cli_e2e_test():
    """步骤 2：执行 CLI 端到端流程（使用多页样本）"""
    print("\n--- 步骤 2: 运行 CLI 端到端测试 ---")
    input_pdf = ROOT_DIR / "tests" / "assets" / "顾炎武全集  14  天下郡国利病书  三_4-6.pdf"
    output_dir = ROOT_DIR / "output"
    output_pdf = output_dir / "e2e_test_result.pdf"

    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)

    command = [
        str(VENV_PYTHON),
        "-m",
        "boocr.cli",
        "poc",
        "--input",
        str(input_pdf),
        "--output",
        str(output_pdf),
    ]
    if not run_command(command):
        print("CLI 端到端测试失败，测试终止。", file=sys.stderr)
        sys.exit(1)

    # 断言输出文件已创建
    if not output_pdf.exists():
        print(f"E2E 测试断言失败：输出文件 {output_pdf} 未创建。", file=sys.stderr)
        sys.exit(1)

    print(f"输出文件已生成: {output_pdf}")
    print("--- CLI 端到端测试通过 ---")
    return True


def generate_coverage_report():
    """步骤 3：生成测试覆盖率报告"""
    print("\n--- 步骤 3: 生成测试覆盖率报告 ---")

    # 确保 pytest-cov 已安装，否则尝试自动安装
    try:
        import pytest_cov  # noqa: F401
    except ImportError:
        print("pytest-cov 未安装，自动安装中...")
        install_ok = run_command([str(VENV_PYTHON), "-m", "pip", "install", "pytest-cov"])
        if not install_ok:
            print("pytest-cov 安装失败，跳过覆盖率报告生成。", file=sys.stderr)
            return False

    coverage_report_dir = ROOT_DIR / "htmlcov"
    command = [
        str(VENV_PYTHON),
        "-m",
        "pytest",
        "--cov=boocr",
        f"--cov-report=html:{coverage_report_dir}",
    ]
    if not run_command(command):
        print("生成覆盖率报告失败。", file=sys.stderr)
        # This is not a critical failure, so we don't exit(1)
        return False

    print(f"覆盖率报告已生成: {coverage_report_dir / 'index.html'}")
    print("--- 覆盖率报告生成完毕 ---")
    return True


def verify_pdf_text_searchability():
    """步骤 4：解析生成 PDF，断言每页可提取文本且长度 > 0"""
    print("\n--- 步骤 4: 验证 PDF 可搜索性 ---")

    if not E2E_OUTPUT_PDF.exists():
        print(f"E2E 测试断言失败：输出文件 {E2E_OUTPUT_PDF} 不存在。", file=sys.stderr)
        sys.exit(1)

    try:
        with pdfplumber.open(str(E2E_OUTPUT_PDF)) as pdf:
            for idx, page in enumerate(pdf.pages):
                # 对竖排文本，pdfplumber.extract_text 可能返回空
                # 使用字符级提取作为后备方案
                text = page.extract_text() or ""
                if len(text.strip()) == 0:
                    # 改用 .chars
                    chars = page.chars
                    text = "".join(ch['text'] for ch in chars)

                if len(text.strip()) == 0:
                    print(
                        f"E2E 测试断言失败：第 {idx + 1} 页无法提取文本或文本为空。",
                        file=sys.stderr,
                    )
                    sys.exit(1)
    except Exception as e:
        print(f"解析 PDF 失败: {e}", file=sys.stderr)
        sys.exit(1)

    print("--- PDF 可搜索性验证通过 ---")
    return True


def _extract_pdf_text(pdf_path: Path) -> str:
    """辅助函数：提取 PDF 中所有页面文字并返回合并后的字符串"""
    texts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_text = (page.extract_text() or "").strip()

            # Fallback to chars if extract_text fails (common for vertical text)
            if not page_text:
                page_text = "".join(ch['text'] for ch in page.chars)

            if page_text:
                texts.append(page_text)
    return "\n".join(texts)


def verify_ocr_conversion_accuracy():
    """步骤 5：基于 expected_simplified.txt 计算相似度 ≥ 90%"""
    print("\n--- 步骤 5: 验证 OCR & 转换准确性 ---")

    if not E2E_OUTPUT_PDF.exists():
        print(f"E2E 测试断言失败：输出文件 {E2E_OUTPUT_PDF} 不存在。", file=sys.stderr)
        sys.exit(1)

    # 提取当前运行生成的简体文字
    current_text = _extract_pdf_text(E2E_OUTPUT_PDF)

    if not current_text.strip():
        print("提取到的简体文字为空，无法比较相似度。", file=sys.stderr)
        sys.exit(1)

    # 如果基线文件不存在，首次运行时自动生成并通过
    if not EXPECTED_TEXT_FILE.exists():
        try:
            EXPECTED_TEXT_FILE.write_text(current_text, encoding="utf-8")
            print(f"基线文件不存在，已自动生成: {EXPECTED_TEXT_FILE}")
            print("首次运行跳过相似度比较，视为通过。")
            return True
        except Exception as e:
            print(f"无法写入基线文件 {EXPECTED_TEXT_FILE}: {e}", file=sys.stderr)
            sys.exit(1)

    expected_text = EXPECTED_TEXT_FILE.read_text(encoding="utf-8")

    # 计算相似度
    similarity = difflib.SequenceMatcher(None, expected_text, current_text).ratio()
    similarity_percent = similarity * 100
    print(f"当前文本与基线文本相似度: {similarity_percent:.2f}%")

    if similarity < 0.90:
        print(
            f"E2E 测试断言失败：相似度 {similarity_percent:.2f}% 低于阈值 90%" ,
            file=sys.stderr,
        )
        sys.exit(1)

    print("--- OCR & 转换准确性验证通过 ---")
    return True


def main():
    """主函数，按顺序执行所有测试步骤"""
    print("="*80)
    print("开始执行集中测试...")
    print("="*80)

    # 步骤 1
    run_unit_tests()

    # 步骤 2
    run_cli_e2e_test()

    # 步骤 3
    generate_coverage_report()

    # 步骤 4
    verify_pdf_text_searchability()

    # 步骤 5
    verify_ocr_conversion_accuracy()

    # 后续步骤将在此处添加

    print("\n" + "="*80)
    print("所有测试执行完毕。")
    print("="*80)


if __name__ == "__main__":
    main()
