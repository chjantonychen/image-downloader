#!/usr/bin/env python3
"""
一键上传到 GitHub
用法: python push_to_github.py <仓库URL> [文件...]
"""

import os
import sys
import subprocess
from pathlib import Path


def run_cmd(cmd, check=True):
    """执行命令"""
    print(f"⚡ 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        print(f"❌ 命令执行失败: {cmd}")
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n示例:")
        print('  python push_to_github.py https://github.com/用户名/仓库名')
        print('  python push_to_github.py https://github.com/用户名/仓库名 file1.py file2.py')
        return

    repo_url = sys.argv[1]
    files = sys.argv[2:] if len(sys.argv) > 2 else []

    workspace = Path(__file__).parent

    # 1. 检查git
    if not run_cmd("git --version", check=False):
        print("❌ Git未安装，请先安装Git: https://git-scm.com/download/win")
        return

    # 2. 检查是否有未保存的文件
    untracked = run_cmd("git status --porcelain", check=False)
    if untracked and not untracked.stdout.strip():
        print("📁 现有文件:")
        print(run_cmd("git status --short", check=False).stdout or "  无变化")

    # 3. 选择要上传的文件
    if not files:
        print("\n📂 当前目录文件:")
        all_files = list(workspace.glob("*.py"))
        for i, f in enumerate(all_files, 1):
            print(f"  {i}. {f.name}")
        print(f"  a. 全部上传")
        print(f"  q. 取消")

        choice = input("\n选择 (数字/a/q): ").strip().lower()
        if choice == 'q':
            return
        elif choice == 'a':
            files = [f.name for f in all_files]
        elif choice.isdigit() and 1 <= int(choice) <= len(all_files):
            files = [all_files[int(choice)-1].name]
        else:
            print("❌ 无效选择")
            return

    # 4. 初始化git（如果需要）
    if not (workspace / ".git").exists():
        print("\n🔧 初始化Git仓库...")
        run_cmd("git init")
        run_cmd("git branch -M main")

    # 5. 添加文件
    print("\n📤 添加文件...")
    for f in files:
        fpath = workspace / f
        if fpath.exists():
            run_cmd(f'git add "{f}"')
            print(f"  ✅ 已添加: {f}")
        else:
            print(f"  ⚠️ 文件不存在: {f}")

    # 6. 提交
    commit_msg = input("\n📝 输入提交说明 (直接回车使用默认): ").strip()
    if not commit_msg:
        commit_msg = f"Add {', '.join(files)}"
    run_cmd(f'git commit -m "{commit_msg}"')

    # 7. 关联远程仓库
    print(f"\n🔗 关联远程仓库...")
    remote_check = run_cmd("git remote -v", check=False)
    if remote_check and "origin" in remote_check.stdout:
        print("  ℹ️ 远程仓库已存在")
    else:
        run_cmd(f'git remote add origin {repo_url}')

    # 8. 推送到GitHub
    print("\n🚀 推送到GitHub...")
    success = run_cmd("git push -u origin main", check=False)

    if success:
        print("\n" + "="*50)
        print("✅ 成功上传到 GitHub!")
        print(f"🔗 访问: {repo_url}")
        print("="*50)
    else:
        print("\n❌ 推送失败，可能原因:")
        print("  1. 需要登录GitHub - 运行: gh auth login")
        print("  2. 或者使用Token认证")
        print("\n💡 提示: 可以先在GitHub创建仓库，然后会显示上传命令")


if __name__ == '__main__':
    main()
