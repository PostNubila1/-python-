# -python-
基于 OCR 的批量视频重命名工具，通过截取视频多个时间点的画面，使用 Windows 自带 OCR 识别课程标题，自动重命名视频文件，并生成日志
# VideoRenamer-OCR

基于 OCR 的批量视频重命名工具，专为中文教育视频设计。通过截取视频多个时间点的画面，使用 Windows 自带 OCR 识别课程标题，自动重命名视频文件，并生成详细的处理日志。

## ✨ 功能特性

- 🎯 **多时间点尝试**：依次截取第 26、15、7、35 秒的画面进行 OCR，提高标题命中率。
- 🧠 **智能提取**：从 OCR 文本中定位“课题/单元/语文”等锚点，刻自己修改，自动截取并清理课程标题。
- 📝 **日志完备**：每个视频的处理过程、OCR 原文、提取结果、新文件名都会保存到 `rename_log.json`，方便核对。
- 🖥️ **零额外模型**：使用 Windows 自带 OCR 引擎，无需下载任何模型，开箱即用。
- 🛡️ **安全保护**：自动过滤无效标题，避免生成垃圾文件名；若提取失败则保留原名。

## 📋 环境要求

- **操作系统**：Windows 10 / 11
- **Python**：3.8 及以上
- **FFmpeg**：已安装并配置好环境变量，或提供绝对路径
- **Python 依赖**：
  - `winocr`
  - `Pillow`

## 🚀 安装步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/yourname/VideoRenamer-OCR.git
   cd VideoRenamer-OCR
   ```

2. **安装 Python 依赖**

   ```bash
   pip install winocr Pillow
   ```

3. **安装 FFmpeg**

   - 下载地址：https://ffmpeg.org/download.html
   - 将 `ffmpeg.exe` 所在目录添加到系统环境变量 `PATH`，或在脚本中配置 `FFMPEG_EXE` 为绝对路径。

## ⚙️ 配置说明

打开 `rename_videos.py`，修改以下配置：

```python
# 目标视频文件夹
VIDEO_DIR = r"D:\xuexishipin\chinese"

# FFmpeg 绝对路径（如果已配置环境变量，可保留默认值 "ffmpeg"）
FFMPEG可执行文件 = r"D: fmpeg\bin fmpeg.exe"

# 尝试截取的时间点（秒）
时间戳 = [26, 15, 7, 35]

# 日志输出路径
日志文件 = os.path.join(视频目录, "重命名日志.json")
```

## 🎬 使用方法

1. 将需要重命名的视频放入 `VIDEO_DIR` 目录。
2. 在命令行中运行：

   ```bash
   python rename_videos.py
   ```
3. 程序会依次处理每个视频：
   - 按 `TIMESTAMPS` 顺序截图并 OCR。
   - 从 OCR 文本中提取课程标题。
   - 若提取成功，则将视频重命名为 `标题.mp4`（若重名则添加 `_1`、`_2` 后缀）。
   - 若所有时间点均无法提取有效标题，则保留原文件名。
4. 处理完成后，控制台会打印每个视频的结果，并生成 `rename_log.json`，包含：
   - `original_name`：原始文件名
   - `ocr`：各时间点的 OCR 原文
   - `extracted_title`：提取出的标题
   - `new_name`：重命名后的文件名
   - `status`：成功 / 跳过
   - `reason`：跳过原因
- **备份原始文件**：批量重命名有风险，建议先备份视频文件。
- **OCR 准确率**：Windows 自带 OCR 对复杂画面、艺术字、模糊文本的识别能力有限，部分视频可能提取失败或标题有误，需要手动修正。
- **文件名冲突**：若多个视频提取出相同标题，程序会自动添加 `_1`、`_2` 后缀，避免覆盖。
- **仅支持 Windows**：`winocr` 依赖 Windows 自带的 OCR 引擎，无法在 macOS / Linux 上运行。

## 📁 仓库结构建议

```
VideoRenamer-OCR/
├── rename_videos.py      # 主脚本
├── requirements.txt      # 依赖列表
├── README.md             # 项目说明
├── LICENSE               # 开源许可证
└── .gitignore            # 忽略临时文件
```

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！如果你有更好的提取规则或 OCR 方案，欢迎分享。

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [FFmpeg](https://ffmpeg.org/) 提供强大的视频处理能力
- [winocr](https://github.com/baicunko/winocr) 封装了 Windows OCR 接口
- 所有为这个项目提供建议和测试的朋友

---

**Enjoy!** 如果这个工具帮到了你，欢迎给个 ⭐️ Star！
