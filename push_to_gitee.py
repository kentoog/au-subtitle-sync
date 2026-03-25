import subprocess
import sys
import os

def run_command(command, check=True):
    """运行外部命令并返回结果"""
    print(f"[*] 执行命令: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] 命令运行失败: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print("=== Gitee 开源同步脚本 ===")
    
    # 1. 添加文件
    if not run_command(["git", "add", "."]):
        return

    # 2. 提交更改
    # 检查是否有需要提交的内容
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
    if status.strip():
        commit_msg = input("[?] 请输入提交信息 (默认: prepare for gitee open source): ").strip()
        if not commit_msg:
            commit_msg = "prepare for gitee open source"
        run_command(["git", "commit", "-m", commit_msg])
    else:
        print("[*] 没有需要提交的更改。")

    # 3. 获取 Gitee 仓库地址
    # 检查是否已添加过 gitee 远程仓库
    remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout
    if "gitee" in remotes.split():
        current_url = subprocess.run(["git", "remote", "get-url", "gitee"], capture_output=True, text=True).stdout.strip()
        print(f"[*] 已检测到远程仓库 'gitee': {current_url}")
        change = input("[?] 是否需要更换地址? (y/N): ").strip().lower()
        if change == 'y':
            new_url = input("[?] 请输入新的 Gitee 仓库地址: ").strip()
            if new_url:
                run_command(["git", "remote", "set-url", "gitee", new_url])
    else:
        gitee_url = input("[?] 请输入 Gitee 仓库地址 (例如 https://gitee.com/user/project.git): ").strip()
        if gitee_url:
            run_command(["git", "remote", "add", "gitee", gitee_url])
        else:
            print("[!] 未提供 URL，跳过远程仓库配置。")
            return

    # 4. 推送
    print("[*] 正在推送到 Gitee...")
    # 这里检测当前分支名
    branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
    if not branch:
        branch = "master"
    
    if run_command(["git", "push", "-u", "gitee", branch]):
        print("\n[√] 同步成功！项目已开源到 Gitee。")
    else:
        print("\n[×] 同步失败，请检查网络或权限设置。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] 操作已取消。")
    except Exception as e:
        print(f"\n[!] 发生错误: {e}")
    
    input("\n按回车键退出...")
