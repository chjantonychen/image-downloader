#!/usr/bin/env python3
"""
网页图片下载器
支持单个URL下载和批量下载
"""

import os
import re
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Set

# 配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
TIMEOUT = 10
MAX_WORKERS = 5  # 并行下载线程数


def get_image_urls(html_content: str, base_url: str) -> Set[str]:
    """从HTML中提取所有图片URL"""
    # 匹配 img 标签的 src 属性
    pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    matches = re.findall(pattern, html_content, re.IGNORECASE)

    image_urls = set()
    for src in matches:
        # 跳过 data URI 和 base64 图片
        if src.startswith('data:'):
            continue
        # 转换为绝对URL
        absolute_url = urljoin(base_url, src)
        image_urls.add(absolute_url)

    return image_urls


def download_image(url: str, save_dir: Path, session: requests.Session) -> tuple:
    """下载单张图片"""
    try:
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        # 从URL提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        # 如果没有文件名，生成一个
        if not filename or '.' not in filename:
            ext = response.headers.get('Content-Type', '').split('/')[-1]
            if ext:
                filename = f"image_{int(time.time())}_{hash(url) % 10000}.{ext}"
            else:
                filename = f"image_{int(time.time())}_{hash(url) % 10000}.jpg"
        else:
            # 限制文件名长度
            filename = filename[:100]

        # 如果文件名重复，添加序号
        save_path = save_dir / filename
        counter = 1
        while save_path.exists():
            name, ext = os.path.splitext(filename)
            save_path = save_dir / f"{name}_{counter}{ext}"
            counter += 1

        # 保存图片
        save_path.write_bytes(response.content)
        return (url, str(save_path), True, None)

    except Exception as e:
        return (url, None, False, str(e))


def download_images_from_url(url: str, save_dir: str = "downloads",
                            parallel: bool = False, max_images: int = 0) -> dict:
    """从指定URL下载所有图片"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"📥 正在获取页面: {url}")

    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ 获取页面失败: {e}")
        return {'success': 0, 'failed': 0, 'errors': [str(e)]}

    # 提取图片URL
    image_urls = get_image_urls(response.text, url)
    print(f"🔍 找到 {len(image_urls)} 张图片")

    if max_images > 0:
        image_urls = list(image_urls)[:max_images]
        print(f"📌 限制下载前 {max_images} 张")

    if not image_urls:
        print("⚠️  未找到任何图片")
        return {'success': 0, 'failed': 0, 'errors': []}

    # 下载图片
    results = {'success': 0, 'failed': 0, 'errors': []}

    if parallel:
        # 并行下载
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(download_image, url, save_dir, session): url
                for url in image_urls
            }
            for future in as_completed(futures):
                url, save_path, success, error = future.result()
                if success:
                    print(f"✅ 已保存: {save_path}")
                    results['success'] += 1
                else:
                    print(f"❌ 下载失败: {url} - {error}")
                    results['failed'] += 1
                    results['errors'].append(f"{url}: {error}")
    else:
        # 顺序下载
        for url in image_urls:
            url, save_path, success, error = download_image(url, save_dir, session)
            if success:
                print(f"✅ 已保存: {save_path}")
                results['success'] += 1
            else:
                print(f"❌ 下载失败: {url} - {error}")
                results['failed'] += 1
                results['errors'].append(f"{url}: {error}")

    print(f"\n📊 完成! 成功: {results['success']}, 失败: {results['failed']}")
    return results


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="网页图片下载器")
    parser.add_argument('url', nargs='?', help='要下载图片的网页URL')
    parser.add_argument('-o', '--output', default='downloads',
                       help='保存目录 (默认: downloads)')
    parser.add_argument('-p', '--parallel', action='store_true',
                       help='启用并行下载')
    parser.add_argument('-m', '--max', type=int, default=0,
                       help='最大下载数量 (0表示不限制)')
    parser.add_argument('-l', '--list', nargs='+',
                       help='从文件或列表读取URL')

    args = parser.parse_args()

    # 如果没有提供URL，显示帮助
    if not args.url and not args.list:
        parser.print_help()
        print("\n💡 示例:")
        print("  python image_downloader.py https://example.com")
        print("  python image_downloader.py https://example.com -o my_images -p")
        print("  python image_downloader.py -l url1.txt url2.txt")
        return

    # 单个URL
    if args.url:
        download_images_from_url(
            args.url,
            save_dir=args.output,
            parallel=args.parallel,
            max_images=args.max
        )

    # 多个URL
    if args.list:
        for url in args.list:
            download_images_from_url(
                url.strip(),
                save_dir=args.output,
                parallel=args.parallel,
                max_images=args.max
            )


if __name__ == '__main__':
    main()
