# 🖼️ Image Downloader

Python网页图片下载器 - 带图形界面

## 功能

- ✅ 从任意网页下载所有图片
- ✅ 支持多线程并行下载
- ✅ 图形界面操作简单
- ✅ 自动过滤非图片文件

## 使用方法

```bash
# 安装依赖
pip install requests

# 运行GUI版本
python image_downloader_gui.py

# 或使用命令行版本
python image_downloader.py https://example.com -p
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `image_downloader_gui.py` | 🖥️ 图形界面版 |
| `image_downloader.py` | 📟 命令行版 |
| `push_to_github.py` | 🔧 上传脚本 |
| `upload_to_github.bat` | 🪟 Windows上传脚本 |

## 界面预览

```
┌─────────────────────────────────────────┐
│ 📥 网页图片下载器                         │
├─────────────────────────────────────────┤
│ 🌐 网页地址                              │
│ URL: https://example.com                 │
│ 保存到: downloads/         [📁 浏览]    │
├─────────────────────────────────────────┤
│ [▶️ 开始下载]  [⏹️ 停止]                 │
└─────────────────────────────────────────┘
```

## 技术栈

- Python 3
- Tkinter (GUI)
- requests (HTTP)
- concurrent.futures (多线程)

## License

MIT
