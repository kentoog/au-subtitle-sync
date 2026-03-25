# AU 字幕外挂同步程序

Adobe Audition 实时字幕同步方案，基于 MIDI-Mackie 桥接方案。

## 功能特性

- 实时接收 Audition 时间轴信号
- 同步显示 LRC 格式字幕
- 独立置顶字幕看板窗口
- 可自定义颜色、字体大小、透明度
- 支持平铺模式和普通模式
- 自动滚动高亮当前播放行

## 环境要求

- Windows 系统
- Python 3.10+
- Adobe Audition
- loopMIDI (虚拟 MIDI 驱动)

## 安装与配置

### 1. 安装虚拟 MIDI 驱动

下载并安装 [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)，创建一个新端口，命名为 `AU_MTC_OUT`。

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 Adobe Audition

1. 打开 `编辑` -> `首选项` -> `操纵面`
2. 点击 `添加`，选择 `Mackie Control`
3. 配置端口：
   - MIDI 输入：无
   - MIDI 输出：选择 `AU_MTC_OUT`

## 使用方法

1. 启动 loopMIDI（确保端口已开启）
2. 启动 Adobe Audition（确保操纵面已配置）
3. 运行主程序：
   ```bash
   python 字幕时间轴接收同步.py
   ```
4. 点击 `加载 LRC` 按钮加载字幕文件
5. 在 Audition 中播放音频，字幕将自动同步

## 项目结构

```
.
├── 字幕时间轴接收同步.py    # 主程序
├── build.py                  # 打包脚本
├── requirements.txt          # Python 依赖
└── README.md                 # 说明文档
```

## 打包成 exe

使用 PyInstaller 打包：

```bash
python build.py
```

## 许可证

MIT License
