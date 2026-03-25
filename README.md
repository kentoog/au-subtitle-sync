# Adobe Audition (AU) 实时字幕同步器 (AU Subtitle Sync)

🎨 **这是一个利用 MIDI 信号实现 Adobe Audition 与外部 LRC 字幕实时同步显示的实用工具。**

由于 Adobe Audition 本身对实时字幕显示的支持有限，本项目通过 **Mackie Control (MIDI)** 协议将 AU 的播放头时间实时同步到外部 Python 悬浮看板中，从而实现高效率的配音、有声书录制或后期字幕校对。



## ✨ 核心特性

- **高精度同步**：基于 MIDI 时间码 (MTC) 的 Mackie 桥接方案，延迟极低。
- **独立置顶窗口**：透明悬浮看板，可缩放、可置顶，适配各种直播或录屏环境。
- **LRC 全面支持**：自动解析标准 LRC 文件，支持逐行滚动。
- **自定义模板**：支持“平铺模式”与“普通模式”切换，自定义前/背景色及字号。
- **多版本适配**：理论上支持所有具备 Mackie Control 输出能力的 Adobe Audition 版本。

---

## 🛠️ 环境准备

### 1. 安装虚拟 MIDI 驱动 (必备)
由于 Audition 不能直接向 Python 脚本发送数据，需要一个“虚拟管道”。

- **推荐软件**：[loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
- **配置步骤**：
  1. 安装并打开 loopMIDI。
  2. 点击 `+` 创建一个新端口，命名为 **`AU_MTC`** (程序会自动查找包含该关键字的任务)。

### 2. Python 环境
本项目需要 Python 3.10+ 环境，运行以下命令安装依赖：

```bash
pip install mido python-rtmidi PyQt6 psutil
```

---

## 🎚️ Adobe Audition 内部配置

这是让 Audition “发送”时间轴数据的关键：

1. 打开 **编辑 (Edit)** -> **首选项 (Preferences)** -> **操纵面 (Control Surface)**。
2. 点击 **添加 (Add)**，在设备类中选择 **Mackie Control**。
3. 点击 **配置 (Configure)**：
   - **MIDI 输入**：保持“无 (None)”。
   - **MIDI 输出**：选择刚才在 loopMIDI 中创建的 **`AU_MTC`** 端口。
4. 点击“确定”保存。此时当你播放音频时，Audition 就会自动广播时间信号。

---

## 🚀 启动与使用

1. **运行程序**：
   ```bash
   python 字幕时间轴接收同步.py
   ```
   或者直接运行打包好的 `AU字幕同步.exe`。

2. **加载字幕**：
   - 点击“加载 LRC”按钮，选择您的 `.lrc` 文件。

3. **开始同步**：
   - 在 Audition 中点击播放，看板会自动跟随时间轴滚动。

4. **个性化调节**：
   - 在主主控界面调节透明度、字号和颜色。
   - 使用“平铺”模式查看更多上下文。

---

## 📦 打包说明

如果您需要打包成单文件 `.exe`，可以使用 PyInstaller：

```bash
pyinstaller --noconsole --onefile --name "AU字幕同步" 字幕时间轴接收同步.py
```

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源。

---

## 🙏 鸣谢

- 感谢开源社区提供的 `mido` 与 `PyQt6`。
- 设计思路参考了专业的 Mackie Control 通讯协议文档。

---

> 如果您觉得本项目对您有帮助，欢迎在 Gitee/GitHub 点个 Star！⭐️
