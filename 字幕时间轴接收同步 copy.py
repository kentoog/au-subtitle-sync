import sys
import re
import mido
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- 1. 极简监听线程：只负责搬运数据，不做复杂解析 ---
class MidiWorker(QThread):
    raw_data_signal = pyqtSignal(str) # 原始字符串信号
    status_signal = pyqtSignal(bool)   

    def run(self):
        # 强制使用 rtmidi 后端（Windows 下最稳定）
        mido.set_backend('mido.backends.rtmidi')
        port_keyword = 'AU_MTC'
        time_display = [" "] * 12
        
        try:
            # 获取端口列表并打印，方便调试
            names = mido.get_input_names()
            print(f"后台线程检测到端口: {names}")
            
            port_name = next((n for n in names if port_keyword in n), None)
            if not port_name:
                self.status_signal.emit(False)
                return

            # open_input 时增加虚拟客户端名称防止冲突
            with mido.open_input(port_name) as inport:
                self.status_signal.emit(True)
                for msg in inport:
                    if msg.type == 'control_change' and 64 <= msg.control <= 75:
                        idx = 75 - msg.control
                        # 直接更新字符
                        time_display[idx] = chr(msg.value)
                        # 拼接并发送，不做任何 int() 转换，防止报错卡死线程
                        raw_str = "".join(time_display)
                        self.raw_data_signal.emit(raw_str)
        except Exception as e:
            print(f"线程崩溃: {e}")
            self.status_signal.emit(False)

# --- 2. 主界面 ---
class LyricPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.lyrics = []
        self.labels = []
        self.init_ui()
        
        self.thread = MidiWorker()
        self.thread.raw_data_signal.connect(self.process_raw_time)
        self.thread.status_signal.connect(self.update_status)
        self.thread.start()

    def init_ui(self):
        self.setWindowTitle("AU 字幕同步 - 强力调试版")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #111; color: white;")

        layout = QVBoxLayout(self)
        
        # 顶部：状态与原始数据监控
        info_layout = QHBoxLayout()
        self.status_label = QLabel("● 扫描中...")
        self.raw_monitor = QLabel("RAW: [等待信号]")
        self.raw_monitor.setStyleSheet("color: yellow; font-family: Consolas;")
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        info_layout.addWidget(self.raw_monitor)
        layout.addLayout(info_layout)

        # 中部：时间换算结果
        self.sec_label = QLabel("秒数: 0.000s")
        self.sec_label.setStyleSheet("font-size: 20px; color: #0f0;")
        layout.addWidget(self.sec_label)

        # 加载按钮
        self.load_btn = QPushButton("加载 LRC")
        self.load_btn.clicked.connect(self.select_file)
        layout.addWidget(self.load_btn)

        # 字幕区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.lyric_layout = QVBoxLayout(self.content)
        self.lyric_layout.setContentsMargins(0, 200, 0, 200)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def update_status(self, ok):
        self.status_label.setText("● 端口就绪" if ok else "● 端口丢失")
        self.status_label.setStyleSheet("color: #0f0;" if ok else "color: red;")

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择LRC", "", "LRC (*.lrc)")
        if path: self.parse_lrc(path)

    def parse_lrc(self, path):
        # 简单的解析实现
        self.lyrics = []
        for lbl in self.labels: lbl.deleteLater()
        self.labels = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                if m:
                    t = int(m.group(1))*60 + float(m.group(2))
                    self.lyrics.append((t, m.group(3).strip()))
                    lbl = QLabel(m.group(3).strip())
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setStyleSheet("color: #444; font-size: 18px;")
                    self.lyric_layout.addWidget(lbl)
                    self.labels.append(lbl)

    def process_raw_time(self, raw_str):
        # 1. 更新原始监控显示
        self.raw_monitor.setText(f"RAW: {raw_str}")
        
        try:
            # 2. 只保留数字，去掉空格和其他杂质
            clean_digits = "".join(filter(str.isdigit, raw_str))
            
            # 如果数字位数太少（刚启动时），先不处理
            if len(clean_digits) < 4: 
                return
            
            # 3. 灵活切片逻辑：
            # 无论前面有多少位，最后3位永远是毫秒，倒数4-5位是秒
            ms_part = int(clean_digits[-3:]) / 1000.0
            ss_part = int(clean_digits[-5:-3])
            
            # 剩余的前面所有位都是分钟
            mm_part_str = clean_digits[:-5]
            mm_part = int(mm_part_str) if mm_part_str else 0
            
            total_seconds = mm_part * 60 + ss_part + ms_part
            
            # 4. 更新界面显示
            self.sec_label.setText(f"秒数: {total_seconds:.3f}s")
            
            # 5. 只有加载了歌词才进行高亮
            if self.lyrics:
                self.update_highlight(total_seconds)
                
        except Exception as e:
            # 如果解析出错，在控制台打印看看是什么字符导致的问题
            print(f"解析解析失败，原始内容: '{raw_str}'，错误: {e}")

    def update_highlight(self, total):
        active_idx = -1
        for i, (t, _) in enumerate(self.lyrics):
            if t <= total: active_idx = i
            else: break
        
        if active_idx != -1:
            for i, lbl in enumerate(self.labels):
                if i == active_idx:
                    lbl.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
                    self.scroll.ensureWidgetVisible(lbl, 0, 150)
                else:
                    lbl.setStyleSheet("color: #444; font-size: 18px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LyricPlayer()
    win.show()
    sys.exit(app.exec())