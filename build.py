import os
import sys
import subprocess
from pathlib import Path

def main():
    # 检查当前目录
    current_dir = Path.cwd()
    print(f"当前工作目录: {current_dir}")
    
    # 检查主程序文件是否存在
    main_script = current_dir / "字幕时间轴接收同步.py"
    if not main_script.exists():
        print(f"错误: 未找到主程序文件 {main_script}")
        sys.exit(1)
    
    # 构建打包命令
    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # 单文件打包
        "--windowed",  # 无控制台窗口
        "--name", "AU字幕同步",  # 输出文件名
        "--distpath", ".",  # 输出到当前目录
        "--workpath", "./build",  # 工作目录
        "--specpath", "./build",  # spec文件目录
        "--hidden-import", "mido.backends.rtmidi", # 显式包含 rtmidi 后端
        "--hidden-import", "rtmidi",               # 显式包含 python-rtmidi
        str(main_script)
    ]
    
    print(f"执行打包命令: {' '.join(command)}")
    
    try:
        # 执行打包命令
        subprocess.run(command, check=True)
        print("\n打包完成!")
        print(f"可执行文件已生成在: {current_dir / 'AU字幕同步.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()