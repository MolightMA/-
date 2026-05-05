<!-- omit in toc -->
# 🌿 英语学习桌面应用

> 基于 PyQt6 + Edge TTS 的智能英语单词学习工具，支持多音色朗读、在线翻译补全、学习进度统计与云端同步。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6.0+-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 功能特性

### 📝 单词管理
- **添加/删除单词** — 快速录入英文与中文释义
- **批量导入** — 支持 TXT 文件导入（格式：`英文,中文` 或 `英文\t中文`）
- **自动翻译补全** — 仅填一侧时自动在线翻译补全另一侧

### 🔊 智能朗读
- **Edge 神经语音** — 微软 Edge 免费高质量 TTS，无需 API Key
- **多音色切换** — 支持多种英语/中文音色自由选择
- **三段式朗读** — `英文 → 中文 → 英文`，强化记忆效果
- **智能合并** — 安装 FFmpeg 时自动合并为单文件播放

### 📊 学习统计
- **环形进度条** — 总词数 / 有音频 / 已同步 三大指标
- **柱状图** — 近 7 天新增单词趋势可视化
- **实时刷新** — 数据变化即时同步到图表

### ☁️ 云端同步
- **上传/拉取同步** — 支持腾讯云开发或自定义 HTTPS 端点
- **离线优先** — 本地 SQLite 数据库，无网络也能正常使用

### 🎨 界面设计
- **薄荷青 + 深色主题** — 护眼配色，专注学习
- **自定义图标** — 支持窗口图标和任务栏图标自定义
- **响应式布局** — 自适应窗口大小

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| GUI 框架 | PyQt6 ≥ 6.6.0 |
| 语音合成 | edge-tts ≥ 6.1.10 |
| 数据库 | SQLite（内置） |
| 音频处理 | pydub + FFmpeg |
| 打包工具 | PyInstaller |
| Python 版本 | 3.10+ |

---

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/MolightMA/-.git
cd 英语
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python main.py
```

### 4. 安装 FFmpeg（可选，推荐）
音频合并功能需要 FFmpeg：
```bash
# Windows (使用 winget)
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

---

## 📦 打包发布

项目已配置 PyInstaller 打包脚本：

```bash
# Windows
.\build_windows.bat

# 或手动打包
python build_release.py
```

打包后的可执行文件位于 `dist/` 目录。

---

## 📂 项目结构

```
英语/
├── main.py              # 应用入口
├── config.py            # 全局配置
├── requirements.txt     # 依赖清单
├── build_windows.bat    # Windows 打包脚本
├── english_learning.spec # PyInstaller 配置文件
├── icon.ico / icon.png  # 应用图标
├── core/                # 核心模块
│   ├── database.py      # SQLite 数据访问
│   ├── tts_engine.py    # Edge TTS 语音合成
│   ├── audio_processor.py   # 音频处理与合并
│   ├── translation.py   # 在线翻译补全
│   ├── cloud_sync.py    # 云端同步
│   └── voice_presets.py # 音色预设
├── ui/                  # 界面模块
│   ├── main_window.py   # 主窗口
│   ├── word_list.py     # 单词列表面板
│   ├── player.py        # 音频播放器
│   ├── stats_chart.py   # 学习统计图表
│   └── theme.py         # 主题样式
└── data/                # 数据目录（运行时生成）
    ├── words.db         # SQLite 数据库
    ├── cache/           # 音频缓存
    └── settings.json     # 用户设置
```

---

## ⚙️ 配置说明

### 语音设置
编辑 `data/settings.json` 自定义音色：
```json
{
  "voice_en": "en-US-JennyNeural",
  "voice_zh": "zh-CN-XiaoxiaoNeural"
}
```

### 云端同步
在 `config.py` 中配置腾讯云开发：
```python
CLOUDBASE_ENABLED = True
CLOUDBASE_SYNC_URL = "你的云函数地址"
CLOUDBASE_API_KEY = "你的API密钥"
```

---

## 🎯 使用技巧

1. **快速添加** — 输入英文和中文后直接回车添加单词
2. **翻译补全** — 只需填一侧，点击"自动翻译补全"填充另一侧
3. **批量导入** — 准备 TXT 文件，每行格式：`apple,苹果`
4. **打乱学习** — 点击"打乱播放顺序"随机播放复习
5. **自定义图标** — 替换 `icon.ico` 和 `icon.png` 即可

---

## 📄 许可证

本项目基于 MIT 许可证开源。

---

## 🙏 致谢

- [PyQt6](https://pypi.org/project/PyQt6/) — 强大的跨平台 GUI 框架
- [edge-tts](https://pypi.org/project/edge-tts/) — 微软 Edge 神经语音接口
- 中国大学生计算机设计大赛参赛项目
