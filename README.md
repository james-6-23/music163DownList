# 🎵 DownList

<div align="center">

<img width="1382" height="1039" alt="PixPin_2025-08-05_17-27-20" src="https://github.com/user-attachments/assets/c5441135-0ad5-4cbb-b9e4-db9ea7a70a98" />


**现代化的网易云音乐下载器**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-UI-green.svg)](https://flet.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](README_EN.md) | 简体中文

</div>

## 📖 项目介绍

DownList 是一个基于 Python 和 Flet 框架开发的现代化网易云音乐下载器，采用 Spotify 风格的深色主题设计。支持批量下载歌单、多种音质选择、歌词下载等功能，提供直观易用的图形界面。

### ✨ 主要特性

- 🎨 **现代化UI设计** - Spotify风格的深色主题界面
- 🎵 **歌单批量下载** - 支持网易云音乐歌单链接解析
- 🎧 **多种音质选择** - 标准/极高/无损/Hi-Res等多种音质
- 📝 **歌词下载** - 可选择同时下载歌词文件
- 🚀 **多线程下载** - 支持1-8个并发下载任务
- 🔍 **歌曲搜索筛选** - 支持按歌曲名、艺术家、专辑搜索
- ✅ **选择性下载** - 可选择特定歌曲进行下载
- 📊 **实时进度显示** - 详细的下载进度和速度显示
- ⏸️ **下载控制** - 支持暂停、继续、取消下载
- 🎯 **元数据嵌入** - 自动添加歌曲信息和封面图片



## 🚀 快速开始

### 环境要求

- Python 3.7 或更高版本
- Windows/macOS/Linux 操作系统
- 网络连接（用于下载音乐）

### 方式一：直接运行源码

```bash
git clone https://github.com/your-username/DownList.git
cd DownList
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 运行程序

```bash
python app.py
```

### 使用可执行文件

如果您不想安装Python环境，可以直接下载并运行打包好的exe文件：

1. 从 [Releases](../../releases) 页面下载最新版本的 `163musicDownList.exe`
2. 双击运行即可，无需安装任何依赖

**注意**:
- exe文件已优化至80-120MB，首次启动可能需要5-8秒
- 如被杀毒软件拦截，请添加到白名单
- 支持Windows 10/11系统

## 📋 使用说明

### 1. 获取Cookie

1. 打开浏览器，访问 [music.163.com](https://music.163.com) 并登录
2. 按 F12 打开开发者工具
3. 切换到 Application/存储 标签
4. 在 Cookies 中找到 `MUSIC_U`，复制其值
5. 将值粘贴到程序的Cookie输入框中

### 2. 下载歌曲

1. **输入歌单链接**：在程序中粘贴网易云音乐歌单链接
2. **选择设置**：
   - 选择音质（标准/极高/无损/Hi-Res等）
   - 选择是否下载歌词
   - 设置下载目录
   - 调整并发下载数量
3. **解析歌单**：点击"解析歌单"按钮
4. **选择歌曲**：可以全选或选择特定歌曲
5. **开始下载**：点击"下载选中"或"下载全部"

### 3. 下载控制

- **暂停/继续**：可以随时暂停或继续下载
- **取消下载**：停止所有下载任务
- **实时监控**：查看下载进度、速度和状态

## 🏗️ 项目结构

```
DownList/
├── api/                    # 网易云音乐API接口
│   └── netease_api.py
├── core/                   # 核心下载逻辑
│   ├── downloader.py
│   └── metadata.py
├── managers/               # 管理器模块
│   ├── cookie_manager.py
│   └── download_manager.py
├── models/                 # 数据模型
│   └── download_task.py
├── ui/                     # 用户界面
│   ├── base_ui.py
│   ├── cookie_ui.py
│   ├── download_ui.py
│   └── enhanced_button_system.py
├── utils/                  # 工具函数
│   ├── constants.py
│   └── file_utils.py
├── assets/                 # 资源文件
│   ├── cookie.png
│   └── display.png
├── app.py                  # 主程序入口
├── requirements.txt       # 依赖列表
├── LICENSE                # 开源许可证
├── README.md              # 中文说明文档
└── README_EN.md           # 英文说明文档
```

## ⚙️ 配置说明

### 音质选项

- **标准音质** (128kbps MP3)
- **极高音质** (320kbps MP3)
- **无损音质** (FLAC)
- **Hi-Res** (高解析度音频)
- **沉浸环绕声** (需要VIP)
- **高清环绕声** (需要VIP)
- **超清母带** (需要VIP)

### 并发设置

- 支持 1-8 个并发下载任务
- 建议根据网络状况调整
- 过高的并发可能导致限流

## 🔧 开发说明

### 技术栈

- **Python 3.7+** - 主要开发语言
- **Flet** - 跨平台UI框架
- **Requests** - HTTP请求库
- **Mutagen** - 音频元数据处理
- **Pillow** - 图像处理
- **Cryptography** - 加密解密

### 架构特点

- **模块化设计** - 清晰的代码结构和职责分离
- **异步下载** - 多线程并发下载支持
- **现代化UI** - Spotify风格的用户界面
- **错误处理** - 完善的异常处理机制
- **日志记录** - 详细的运行日志

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守相关法律法规：

- 下载的音乐仅供个人学习和欣赏使用
- 请勿用于商业用途或公开传播
- 建议支持正版音乐，购买官方音乐服务
- 使用本工具产生的任何法律问题由用户自行承担

## 📋 版本信息

### 当前版本: v2.0.0

### 更新日志

#### v2.0.0 (2025-01-05)
- 🎨 全新的 Spotify 风格 UI 设计
- 🚀 增强的按钮系统和用户体验
- 📱 优化的窗口尺寸 (1400×1100)
- 🔧 重构的代码架构，提高维护性
- 🐛 修复了多个已知问题
- ⚡ 性能优化和稳定性改进

#### v1.x.x
- 基础功能实现
- 网易云音乐歌单下载
- 多线程下载支持
- 基础 UI 界面

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

### 贡献指南

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📞 联系方式

如果您有任何问题或建议，请通过以下方式联系：

- 提交 [Issue](../../issues)
- 发起 [Discussion](../../discussions)

---

<div align="center">

**如果这个项目对您有帮助，请给它一个 ⭐ Star！**

</div>
