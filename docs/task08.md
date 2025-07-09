# 任务 #8【CI-release】详细规划

## 一、目标  
1. 当代码仓库创建版本标签（如 v0.3.0）时：  
   ① 触发 GitHub Actions。  
   ② 重新执行 lint / test / build（复用已写好的三个 job）。  
   ③ 生成跨平台二进制（至少 Windows、Linux x86_64，可选 macOS）。  
   ④ 自动创建 GitHub Release，并把二进制和校验文件上传。  
2. Release 成功后，CI 给出 ✅ 状态；失败则整个 workflow 标红并阻断。

## 二、拆解子任务  
1. workflow 文件  
   - 新建 `.github/workflows/release.yml`，事件触发使用 `push: tags: ['v*.*.*']`。  
   - 复用 `lint`、`test` 两个 job，或直接 `needs: [build]` 让 build 失败即终止。  
2. build job  
   - 运行矩阵策略：  
     ```yaml
     strategy:
       matrix:
         include:
           - os: ubuntu-latest
             artifact_name: boocr-linux-amd64.tar.gz
           - os: windows-latest
             artifact_name: boocr-windows-amd64.zip
     ```  
   - 安装 Poetry、PyInstaller（你的 `CI-build` job 已做，可直接复用）。  
   - 打包脚本：`pyinstaller boocr.spec`。  
   - 将 dist 目录重新打包成上述 `artifact_name` 并上传 `actions/upload-artifact`。  
3. create-release job  
   - 使用 `softprops/action-gh-release`；`needs: build`。  
   - 下载每个平台的 artifact，再通过 `softprops/action-gh-release` 的 `files` 参数上传。  
     ```yaml
     with:
       files: |
         boocr-linux-amd64.tar.gz
         boocr-windows-amd64.zip
     ```  
   - title/body 可以自动生成，或读取 `CHANGELOG.md`（如有）。  
4. 校验文件（可选增强）  
   - 打包完成后生成 SHA256：`sha256sum *.tar.gz > checksums.txt` 并一并上传。  
5. 版本号同步  
   - 在 `book_ocr/__init__.py` 中维护 `__version__`。  
   - 在 CI 里用 `python -c "import book_ocr, sys; v=book_ocr.__version__; assert v==os.environ['GITHUB_REF_NAME'].lstrip('refs/tags/v')"` 保证标签与代码一致。  
6. 流程本地演练  
   - 使用 `gh workflow run` 或创建一个临时 tag `v0.0.0-rc` 推到 fork，观察 release 是否生成且附件完整。  

## 三、代码与文档更新  
1. 新增 / 修改文件  
   - `.github/workflows/release.yml`  
   - `book_ocr/__init__.py` 确保含版本号。  
   - （可选）`CHANGELOG.md`。  
2. 更新 `docs/tasks.md`  
   - 将 #8 标记为 √，并把 「→ 指针」移动到 #9。  

## 四、验收标准  
- 推送 tag 后，GitHub Actions 显示绿色；Release 页面出现对应版本，含两个二进制包与 checksums。  
- 下载包能在目标 OS 上运行 `boocr --version` 输出正确版本。  
- `docs/tasks.md` 进度已同步。 