# 🎵 DownList

<div align="center">



**Modern NetEase Cloud Music Downloader**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-UI-green.svg)](https://flet.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [简体中文](README.md)

</div>

## 📖 Introduction

DownList is a modern NetEase Cloud Music downloader built with Python and Flet framework, featuring a Spotify-style dark theme design. It supports batch playlist downloads, multiple audio quality options, lyrics downloading, and provides an intuitive graphical user interface.

### ✨ Key Features

- 🎨 **Modern UI Design** - Spotify-style dark theme interface
- 🎵 **Batch Playlist Download** - Support for NetEase Cloud Music playlist links
- 🎧 **Multiple Audio Quality** - Standard/High/Lossless/Hi-Res and more
- 📝 **Lyrics Download** - Optional lyrics file download
- 🚀 **Multi-threaded Download** - Support for 1-8 concurrent download tasks
- 🔍 **Song Search & Filter** - Search by song name, artist, or album
- ✅ **Selective Download** - Choose specific songs to download
- 📊 **Real-time Progress** - Detailed download progress and speed display
- ⏸️ **Download Control** - Support pause, resume, and cancel operations
- 🎯 **Metadata Embedding** - Automatic song information and cover art embedding


## 🚀 Quick Start

### Requirements

- Python 3.7 or higher
- Windows OS (recommended)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Program

```bash
# Method 1: Run main program (recommended)
python app.py

# Method 2: Use new entry point
python main_new.py

# Method 3: Original version (backward compatible)
python main.py
```

### Use Executable File

If you don't want to install Python environment, you can directly download and run the packaged exe file:

1. Download the latest `163musicDownList.exe` from [Releases](../../releases) page
2. Double-click to run, no dependencies required

## 📋 Usage Guide

### 1. Get Cookie

1. Open browser and visit [music.163.com](https://music.163.com), then login
2. Press F12 to open developer tools
3. Switch to Application/Storage tab
4. Find `MUSIC_U` in Cookies and copy its value
5. Paste the value into the program's Cookie input box

### 2. Download Songs

1. **Input Playlist Link**: Paste NetEase Cloud Music playlist link
2. **Choose Settings**:
   - Select audio quality (Standard/High/Lossless/Hi-Res, etc.)
   - Choose whether to download lyrics
   - Set download directory
   - Adjust concurrent download count
3. **Parse Playlist**: Click "Parse Playlist" button
4. **Select Songs**: Select all or specific songs
5. **Start Download**: Click "Download Selected" or "Download All"

### 3. Download Control

- **Pause/Resume**: Pause or resume downloads anytime
- **Cancel Download**: Stop all download tasks
- **Real-time Monitor**: View download progress, speed, and status

## 🏗️ Project Structure

```
DownList/
├── api/                    # NetEase Cloud Music API
│   └── netease_api.py
├── core/                   # Core download logic
│   ├── downloader.py
│   └── metadata.py
├── managers/               # Manager modules
│   ├── cookie_manager.py
│   └── download_manager.py
├── models/                 # Data models
│   └── download_task.py
├── ui/                     # User interface
│   ├── base_ui.py
│   ├── cookie_ui.py
│   └── download_ui.py
├── utils/                  # Utility functions
│   ├── constants.py
│   └── file_utils.py
├── assets/                 # Resource files
├── app.py                  # Main program entry
├── main_new.py            # New entry point
├── main.py                # Original entry (compatible)
└── requirements.txt       # Dependencies list
```

## ⚙️ Configuration

### Audio Quality Options

- **Standard Quality** (128kbps MP3)
- **High Quality** (320kbps MP3)
- **Lossless Quality** (FLAC)
- **Hi-Res** (High Resolution Audio)
- **Immersive Surround** (VIP required)
- **HD Surround** (VIP required)
- **Ultra HD Master** (VIP required)

### Concurrency Settings

- Support 1-8 concurrent download tasks
- Adjust based on network conditions
- Too high concurrency may cause rate limiting

## 🔧 Development

### Tech Stack

- **Python 3.7+** - Main development language
- **Flet** - Cross-platform UI framework
- **Requests** - HTTP request library
- **Mutagen** - Audio metadata processing
- **Pillow** - Image processing
- **Cryptography** - Encryption and decryption

### Architecture Features

- **Modular Design** - Clear code structure and separation of concerns
- **Asynchronous Download** - Multi-threaded concurrent download support
- **Modern UI** - Spotify-style user interface
- **Error Handling** - Comprehensive exception handling mechanism
- **Logging** - Detailed runtime logging

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please comply with relevant laws and regulations:

- Downloaded music is for personal study and appreciation only
- Do not use for commercial purposes or public distribution
- Support genuine music by purchasing official music services
- Users are responsible for any legal issues arising from the use of this tool

## 🤝 Contributing

Issues and Pull Requests are welcome to improve this project!

## 📞 Contact

If you have any questions or suggestions, please contact us through:

- Submit an [Issue](../../issues)
- Start a [Discussion](../../discussions)

---

<div align="center">

**If this project helps you, please give it a ⭐ Star!**

</div>
