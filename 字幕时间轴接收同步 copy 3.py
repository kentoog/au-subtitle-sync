import sys
import re
import mido
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QSlider, QTextEdit, QColorDialog, QFrame, QStyle, QStyleOption)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QPainter

# --- 1. MIDI 监听线程 (保持稳定) ---
class MidiWorker(QThread):
    raw_data_signal = pyqtSignal(str)
    status_signal = pyqtSignal(bool)

    def run(self):
        mido.set_backend('mido.backends.rtmidi')
        port_keyword = 'AU_MTC'
        time_display = [" "] * 12
        try:
            names = mido.get_input_names()
            port_name = next((n for n in names if port_keyword in n), None)
            if not port_name:
                self.status_signal.emit(False)
                return
            with mido.open_input(port_name) as inport:
                self.status_signal.emit(True)
                for msg in inport:
                    if msg.type == 'control_change' and 64 <= msg.control <= 75:
                        time_display[75 - msg.control] = chr(msg.value)
                        self.raw_data_signal.emit("".join(time_display))
        except Exception as e:
            print(f"MIDI 启动失败: {e}")
            self.status_signal.emit(False)

# --- 2. 独立置顶字幕窗口 ---
class DetachableLyricWindow(QFrame):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("同步字幕看板")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.text_editor = QTextEdit()
        self.text_editor.setReadOnly(True)
        self.text_editor.setUndoRedoEnabled(False)
        self.text_editor.setFrameStyle(0)
        self.text_editor.setStyleSheet("background: transparent; border: none; color: #666; selection-background-color: rgba(255, 255, 255, 30);")
        self.text_editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth) # 确保根据宽度换行
        layout.addWidget(self.text_editor)
        
        self.resize(600, 400)
        self.setMouseTracking(True) # 开启鼠标追踪以检测边缘
        self.m_drag = False
        self.m_resize_dir = None
        self.m_margin = 10 # 热区宽度
        self.m_op = 1.0
        self.m_hovered = False

    def get_resize_dir(self, pos):
        """检测鼠标是否在窗口边缘以确定缩放方向"""
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        direction = ""
        if y < self.m_margin: direction += "T"
        elif y > h - self.m_margin: direction += "B"
        if x < self.m_margin: direction += "L"
        elif x > w - self.m_margin: direction += "R"
        return direction

    def update_cursor(self, direction):
        if direction in ["TL", "BR"]: self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif direction in ["TR", "BL"]: self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif "T" in direction or "B" in direction: self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif "L" in direction or "R" in direction: self.setCursor(Qt.CursorShape.SizeHorCursor)
        else: self.setCursor(Qt.CursorShape.ArrowCursor)

    def update_bg_opacity(self, op):
        self.m_op = op
        self.refresh_style()

    def refresh_style(self):
        border = "1px solid #555" if self.m_hovered else "1px solid transparent"
        self.setStyleSheet(f"QFrame {{ background-color: rgba(18, 18, 18, {int(self.m_op * 255)}); border-radius: 12px; border: {border}; }}")

    def enterEvent(self, event):
        self.m_hovered = True
        self.refresh_style()

    def leaveEvent(self, event):
        self.m_hovered = False
        self.refresh_style()

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

    # 鼠标事件处理：支持缩放和拖拽
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self.m_resize_dir = self.get_resize_dir(pos)
            if self.m_resize_dir:
                self.m_start_rect = self.geometry()
                self.m_start_pos = event.globalPosition().toPoint()
            else:
                self.m_drag = True
                self.m_DragPosition = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()
        
        if not event.buttons():
            # 未按下鼠标时，更新光标样式
            direction = self.get_resize_dir(pos)
            self.update_cursor(direction)
        
        elif event.buttons() == Qt.MouseButton.LeftButton:
            if self.m_resize_dir:
                # 缩放逻辑
                rect = self.m_start_rect
                diff = global_pos - self.m_start_pos
                new_rect = list([rect.x(), rect.y(), rect.width(), rect.height()])
                
                if "T" in self.m_resize_dir:
                    new_rect[1] += diff.y()
                    new_rect[3] -= diff.y()
                elif "B" in self.m_resize_dir:
                    new_rect[3] += diff.y()
                
                if "L" in self.m_resize_dir:
                    new_rect[0] += diff.x()
                    new_rect[2] -= diff.x()
                elif "R" in self.m_resize_dir:
                    new_rect[2] += diff.x()
                
                # 限制最小尺寸
                if new_rect[2] > 100 and new_rect[3] > 60:
                    self.setGeometry(new_rect[0], new_rect[1], new_rect[2], new_rect[3])
            
            elif self.m_drag:
                # 移动逻辑
                self.move(global_pos - self.m_DragPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.m_drag = False
        self.m_resize_dir = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        # 释放鼠标时保存一次位置，防止意外崩溃
        QSettings("MyStudio", "AUSyncLyrics").setValue("lyric_geom", self.saveGeometry())

# --- 3. 主控制程序 ---
class LyricMasterControl(QWidget):
    def __init__(self):
        super().__init__()
        # 初始化 QSettings (公司名, 应用名)
        self.settings = QSettings("MyStudio", "AUSyncLyrics")
        
        self.lyrics = []
        self.current_idx = -1
        self.last_update_time = 0
        
        # 加载保存的配置
        self.color_active = self.settings.value("color_active", "#00FF00")
        self.color_normal = self.settings.value("color_normal", "#666666")
        self.main_op = float(self.settings.value("main_op", 1.0))
        self.lyric_op = float(self.settings.value("lyric_op", 1.0))
        self.font_size_active = int(self.settings.value("font_size_active", 32))
        self.font_size_normal = int(self.settings.value("font_size_normal", 18))

        self.lyric_win = DetachableLyricWindow()
        self.init_ui()
        
        # 应用初始配置
        self.setWindowOpacity(self.main_op)
        self.lyric_win.update_bg_opacity(self.lyric_op)
        
        # 恢复上次看板的位置和大小
        geom = self.settings.value("lyric_geom")
        if geom: self.lyric_win.restoreGeometry(geom)
        
        self.thread = MidiWorker()
        self.thread.raw_data_signal.connect(self.process_time)
        self.thread.status_signal.connect(self.update_status)
        self.thread.start()

    def closeEvent(self, event):
        """主程序关闭时同步关闭看板并保存位置大小"""
        self.settings.setValue("lyric_geom", self.lyric_win.saveGeometry())
        self.lyric_win.close()
        event.accept()

    def init_ui(self):
        self.setWindowTitle("AU 主控播放同步LRC字幕")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #222; color: #BBB; font-family: 'Microsoft YaHei';")
        self.setFixedWidth(320) # 缩小主程序宽度

        # 主布局紧凑化
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 10) # 减小边距
        main_layout.setSpacing(8) # 减小控件间距

        # 1. 状态栏 (紧凑型)
        top_bar = QHBoxLayout()
        self.status_lbl = QLabel("● 扫描中")
        self.status_lbl.setStyleSheet("font-size: 11px;")
        self.time_lbl = QLabel("0.000s")
        self.time_lbl.setStyleSheet("color: #0F0; font-family: Consolas; font-size: 13px;")
        top_bar.addWidget(self.status_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.time_lbl)
        main_layout.addLayout(top_bar)

        # 2. 控制参数 (透明度与字号)
        def create_slider(label_text, current_val, callback, min_v=0, max_v=100):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(55) # 统一标签宽度
            lbl.setStyleSheet("font-size: 11px;")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(int(current_val))
            slider.setFixedHeight(15)
            slider.valueChanged.connect(callback)
            row.addWidget(lbl)
            row.addWidget(slider)
            return row

        main_layout.addLayout(create_slider("主控透明:", self.main_op * 100, self.update_main_op, 20, 100))
        main_layout.addLayout(create_slider("看板透明:", self.lyric_op * 100, self.update_lyric_op, 0, 100))
        main_layout.addLayout(create_slider("字号(常):", self.font_size_normal, self.update_font_size_normal, 10, 80))
        main_layout.addLayout(create_slider("字号(当):", self.font_size_active, self.update_font_size_active, 10, 120))

        # 3. 颜色与功能键
        btn_style = "background: #333; border: 1px solid #444; padding: 4px; font-size: 11px;"
        
        color_row = QHBoxLayout()
        self.btn_act = QPushButton("当前色")
        self.btn_norm = QPushButton("常规色")
        for b in [self.btn_act, self.btn_norm]: b.setStyleSheet(btn_style)
        self.btn_act.clicked.connect(lambda: self.pick_color('active'))
        self.btn_norm.clicked.connect(lambda: self.pick_color('normal'))
        color_row.addWidget(self.btn_act)
        color_row.addWidget(self.btn_norm)
        main_layout.addLayout(color_row)

        func_row = QHBoxLayout()
        self.btn_top = QPushButton("看板置顶: 开")
        self.btn_top.setCheckable(True)
        self.btn_top.setChecked(True)
        self.btn_top.setStyleSheet(btn_style)
        self.btn_top.clicked.connect(self.toggle_top_hint)
        self.btn_detach = QPushButton("🔓 开启/隐藏看板")
        self.btn_detach.setStyleSheet(btn_style)
        self.btn_detach.clicked.connect(self.toggle_sub_win)
        func_row.addWidget(self.btn_top)
        func_row.addWidget(self.btn_detach)
        main_layout.addLayout(func_row)

        self.btn_load = QPushButton("加载 LRC")
        self.btn_load.setStyleSheet("background: #444; font-weight: bold; height: 30px;")
        self.btn_load.clicked.connect(self.load_lrc)
        main_layout.addWidget(self.btn_load)


    # --- 配置保存逻辑 ---
    def update_main_op(self, v):
        op = v / 100.0
        self.setWindowOpacity(op)
        self.settings.setValue("main_op", op)

    def update_lyric_op(self, v):
        op = v / 100.0
        self.lyric_op = op
        self.lyric_win.update_bg_opacity(op)
        self.settings.setValue("lyric_op", op)

    def update_font_size_normal(self, v):
        self.font_size_normal = v
        self.settings.setValue("font_size_normal", v)
        self.refresh_text_display()
        if self.current_idx != -1: self.update_highlight(self.last_update_time, force=True)

    def update_font_size_active(self, v):
        self.font_size_active = v
        self.settings.setValue("font_size_active", v)
        if self.current_idx != -1: self.update_highlight(self.last_update_time, force=True)

    def toggle_top_hint(self):
        checked = self.btn_top.isChecked()
        self.btn_top.setText(f"📌 看板置顶: {'开' if checked else '关'}")
        flags = Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        if checked: flags |= Qt.WindowType.WindowStaysOnTopHint
        self.lyric_win.setWindowFlags(flags)
        self.lyric_win.show() # 设置 Flags 后窗口会隐藏，需要重新 show

    def pick_color(self, target):
        color = QColorDialog.getColor(QColor(self.color_active if target=='active' else self.color_normal))
        if color.isValid():
            hex_color = color.name()
            if target == 'active': 
                self.color_active = hex_color
                self.settings.setValue("color_active", hex_color)
            else: 
                self.color_normal = hex_color
                self.settings.setValue("color_normal", hex_color)
            self.refresh_text_display()

    # --- 字幕渲染与 MIDI 处理 (保持逻辑) ---
    def toggle_sub_win(self):
        if self.lyric_win.isVisible(): self.lyric_win.hide()
        else: self.lyric_win.show()

    def load_lrc(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择LRC", "", "LRC (*.lrc)")
        if not path: return
        self.lyrics = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                if m:
                    t = int(m.group(1))*60 + float(m.group(2))
                    self.lyrics.append((t, m.group(3).strip()))
        self.refresh_text_display()
        self.lyric_win.show() # 加载后默认开启看板

    def refresh_text_display(self):
        """同步重置全量文本的基础格式"""
        self.lyric_win.text_editor.clear()
        
        # 批量设置常规样式（防止跨行框选时颜色混乱）
        cursor = self.lyric_win.text_editor.textCursor()
        fmt_norm = QTextCharFormat()
        fmt_norm.setForeground(QColor(self.color_normal))
        fmt_norm.setFontPointSize(self.font_size_normal)
        
        for _, txt in self.lyrics:
            cursor.insertText(txt + "\n", fmt_norm)
            
        # 设置全体居中对齐
        self.lyric_win.text_editor.selectAll()
        self.lyric_win.text_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 清除选中状态
        c = self.lyric_win.text_editor.textCursor()
        c.clearSelection()
        self.lyric_win.text_editor.setTextCursor(c)

    def process_time(self, raw_str):
        try:
            d = "".join(filter(str.isdigit, raw_str))
            if len(d) < 4: return
            total = (int(d[:-5]) if len(d)>5 else 0)*60 + int(d[-5:-3]) + int(d[-3:])/1000.0
            self.time_lbl.setText(f"{total:.3f}s")
            if self.lyrics and abs(total - self.last_update_time) > 0.04:
                self.update_highlight(total)
                self.last_update_time = total
        except: pass

    def update_highlight(self, total, force=False):
        if not self.lyrics: return
        idx = -1
        # 寻找当前时间对应的歌词行
        for i, (t, _) in enumerate(self.lyrics):
            if t <= total: idx = i
            else: break
            
        # 如果索引改变，或者强制刷新（如字号改变）
        if idx != -1 and (idx != self.current_idx or force):
            editor = self.lyric_win.text_editor
            doc = editor.document()
            
            # 1. 恢复旧行的样式 (如果是正常切换)
            if self.current_idx != -1 and self.current_idx < len(self.lyrics) and self.current_idx != idx:
                old_block = doc.findBlockByNumber(self.current_idx)
                if old_block.isValid():
                    cursor = QTextCursor(old_block)
                    cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(self.color_normal))
                    fmt.setFontPointSize(self.font_size_normal)
                    cursor.setCharFormat(fmt)

            # 更新当前索引
            self.current_idx = idx
            
            # 2. 应用当前行高亮样式 (直接修改字符格式以支持字号)
            block = doc.findBlockByNumber(idx)
            if block.isValid():
                cursor = QTextCursor(block)
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(self.color_active))
                fmt.setFontPointSize(self.font_size_active)
                fmt.setFontWeight(QFont.Weight.Bold)
                cursor.setCharFormat(fmt)
                
                # 重新应用居中对齐 (防止 setCharFormat 干扰对齐)
                block_fmt = block.blockFormat()
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cursor.setBlockFormat(block_fmt)

                # --- 步骤 B: 强制视觉居中算法 ---
                v_bar = editor.verticalScrollBar()
                viewport_height = editor.viewport().height()
                # 获取行在视图中的矩形位置
                rect = editor.cursorRect(cursor)
                line_pos_y = rect.top()
                
                # 计算目标滚动值
                target_scroll = v_bar.value() + line_pos_y - (viewport_height / 2) + 25
                v_bar.setValue(int(target_scroll))

    def update_status(self, ok):
        self.status_lbl.setText("● 就绪" if ok else "● 离线")
        self.status_lbl.setStyleSheet("color: #0f0;" if ok else "color: red;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ctrl = LyricMasterControl()
    ctrl.show()
    sys.exit(app.exec())