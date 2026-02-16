#!/usr/bin/env python3
"""
网页图片下载器 - 图形界面版
"""

import os
import re
import threading
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
import requests
from tkinter import (
    Tk, StringVar, BooleanVar, IntVar,
    Entry, Button, Label, Text, Scrollbar,
    Listbox, Spinbox, Checkbutton, Frame,
    filedialog, messagebox, ttk
)
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
TIMEOUT = 10
MAX_WORKERS = 5


class ImageDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📥 网页图片下载器")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        self.session = requests.Session()
        self.downloading = False

        # 变量
        self.url_var = StringVar()
        self.save_dir_var = StringVar(value=str(Path.cwd() / "downloads"))
        self.parallel_var = BooleanVar(value=False)
        self.max_images_var = IntVar(value=0)
        self.status_var = StringVar(value="就绪")

        self.setup_ui()

    def setup_ui(self):
        """构建界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # ========== URL输入区域 ==========
        url_frame = ttk.LabelFrame(main_frame, text="🌐 网页地址", padding="10")
        url_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(url_frame, text="URL:").pack(anchor="w")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=70)
        url_entry.pack(fill="x", pady=5)

        # ========== 保存路径 ==========
        path_frame = ttk.Frame(url_frame)
        path_frame.pack(fill="x", pady=5)

        ttk.Label(path_frame, text="保存到:").pack(side="left")
        path_entry = ttk.Entry(path_frame, textvariable=self.save_dir_var, width=55)
        path_entry.pack(side="left", padx=5)
        ttk.Button(path_frame, text="📁 浏览", command=self.browse_folder).pack(side="left")

        # ========== 选项区域 ==========
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ 选项", padding="10")
        options_frame.pack(fill="x", pady=(0, 10))

        # 左边：并行下载
        ttk.Checkbutton(options_frame, text="🚀 并行下载 (多线程)",
                       variable=self.parallel_var).pack(side="left", padx=10)

        # 右边：最大数量
        ttk.Label(options_frame, text="最大数量:").pack(side="left", padx=(20, 5))
        spinbox = Spinbox(options_frame, from_=0, to=999, textvariable=self.max_images_var, width=8)
        spinbox.pack(side="left")
        ttk.Label(options_frame, text="(0=不限)").pack(side="left")

        # ========== 按钮区域 ==========
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)

        self.start_btn = ttk.Button(btn_frame, text="▶️ 开始下载", command=self.start_download)
        self.start_btn.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="⏹️ 停止", command=self.stop_download).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空日志", command=self.clear_log).pack(side="right", padx=5)

        # ========== 进度条 ==========
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=5)

        self.progress_var = StringVar(value="0/0")
        ttk.Label(progress_frame, textvariable=self.progress_var, width=10).pack(side="left")
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.percent_var = StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.percent_var, width=8).pack(side="left")

        # ========== 状态 ==========
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=5)
        ttk.Label(status_frame, text="状态:").pack(side="left")
        ttk.Label(status_frame, textvariable=self.status_var, foreground="blue").pack(side="left", padx=5)

        # ========== 日志区域 ==========
        log_frame = ttk.LabelFrame(main_frame, text="📋 下载日志", padding="5")
        log_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 日志文本框 + 滚动条
        log_text = Text(log_frame, height=15, wrap="word", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        log_text.pack(side="left", fill="both", expand=True)
        self.log_text = log_text

        # ========== 下载列表 ==========
        list_frame = ttk.LabelFrame(main_frame, text="📁 已下载文件", padding="5")
        list_frame.pack(fill="x")

        file_list = Listbox(list_frame, height=5, font=("Consolas", 9))
        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=file_list.yview)
        file_list.configure(yscrollcommand=list_scrollbar.set)

        list_scrollbar.pack(side="right", fill="y")
        file_list.pack(side="left", fill="x", expand=True)
        self.file_list = file_list

    def browse_folder(self):
        """选择保存文件夹"""
        folder = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if folder:
            self.save_dir_var.set(folder)

    def log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")

    def get_image_urls(self, html_content: str, base_url: str):
        """提取图片URL"""
        pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        image_urls = set()
        for src in matches:
            if src.startswith('data:'):
                continue
            absolute_url = urljoin(base_url, src)
            image_urls.add(absolute_url)

        return image_urls

    def download_single_image(self, url: str, save_dir: Path):
        """下载单张图片"""
        try:
            response = self.session.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()

            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or f"image_{int(time.time())}_{hash(url) % 10000}"

            # 检查是否为有效图片
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                return None, None, False, "非图片类型"

            # 获取扩展名
            ext = content_type.split('/')[-1]
            if ext and ';' in ext:
                ext = ext.split(';')[0].strip()
            if not filename.endswith(f".{ext}"):
                filename += f".{ext}"

            # 避免文件名重复
            save_path = save_dir / filename
            counter = 1
            while save_path.exists():
                name, ext_name = os.path.splitext(filename)
                save_path = save_dir / f"{name}_{counter}{ext_name}"
                counter += 1

            save_path.write_bytes(response.content)
            return url, str(save_path), True, None

        except Exception as e:
            return url, None, False, str(e)

    def start_download(self):
        """开始下载"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入网页URL")
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        save_dir = Path(self.save_dir_var.get())
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)

        # UI状态
        self.downloading = True
        self.start_btn.configure(state="disabled")
        self.file_list.delete(0, "end")
        self.log("=" * 50)
        self.log(f"🌐 开始下载: {url}")

        # 在新线程中执行
        threading.Thread(target=self.download_thread, args=(url, save_dir), daemon=True).start()

    def download_thread(self, url: str, save_dir: Path):
        """下载线程"""
        try:
            # 获取页面
            self.status_var.set("正在获取页面...")
            response = self.session.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()

            # 提取图片
            image_urls = self.get_image_urls(response.text, url)
            total = len(image_urls)

            if total == 0:
                self.log("⚠️ 未找到任何图片")
                self.status_var.set("未找到图片")
                self.finish_download()
                return

            # 限制数量
            max_images = self.max_images_var.get()
            if max_images > 0 and total > max_images:
                image_urls = list(image_urls)[:max_images]
                total = max_images

            self.log(f"🔍 找到 {total} 张图片")

            # 更新进度条
            self.progress_bar["maximum"] = total
            success_count = 0
            failed_count = 0
            downloaded_files = []

            # 下载
            if self.parallel_var.get():
                # 并行下载
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {
                        executor.submit(self.download_single_image, url, save_dir): url
                        for url in image_urls
                    }
                    for i, future in enumerate(as_completed(futures), 1):
                        if not self.downloading:
                            break
                        img_url, save_path, success, error = future.result()
                        if success:
                            self.log(f"✅ {os.path.basename(save_path)}")
                            self.file_list.insert("end", os.path.basename(save_path))
                            downloaded_files.append(save_path)
                            success_count += 1
                        else:
                            self.log(f"❌ {img_url[:50]}... - {error}")
                            failed_count += 1
                        self.progress_bar["value"] = i
                        self.progress_var.set(f"{i}/{total}")
                        percent = int(i / total * 100)
                        self.percent_var.set(f"{percent}%")
                        self.status_var.set(f"下载中... {i}/{total}")
            else:
                # 顺序下载
                for i, img_url in enumerate(image_urls, 1):
                    if not self.downloading:
                        break
                    img_url, save_path, success, error = self.download_single_image(img_url, save_dir)
                    if success:
                        self.log(f"✅ {os.path.basename(save_path)}")
                        self.file_list.insert("end", os.path.basename(save_path))
                        downloaded_files.append(save_path)
                        success_count += 1
                    else:
                        self.log(f"❌ {img_url[:50]}... - {error}")
                        failed_count += 1
                    self.progress_bar["value"] = i
                    self.progress_var.set(f"{i}/{total}")
                    percent = int(i / total * 100)
                    self.percent_var.set(f"{percent}%")
                    self.status_var.set(f"下载中... {i}/{total}")

            # 完成
            self.log(f"\n📊 完成! 成功: {success_count}, 失败: {failed_count}")
            self.status_var.set(f"完成! 成功 {success_count} 张")
            self.log(f"📁 保存位置: {save_dir}")

        except requests.RequestException as e:
            self.log(f"❌ 网络错误: {e}")
            self.status_var.set("网络错误")
        except Exception as e:
            self.log(f"❌ 错误: {e}")
            self.status_var.set("发生错误")
        finally:
            self.finish_download()

    def finish_download(self):
        """完成下载"""
        self.downloading = False
        self.start_btn.configure(state="normal")

    def stop_download(self):
        """停止下载"""
        if self.downloading:
            self.downloading = False
            self.log("⏹️ 用户取消下载")
            self.status_var.set="已取消"
            self.finish_download()


def main():
    root = Tk()
    app = ImageDownloaderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
