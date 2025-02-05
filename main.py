import os
import random
import subprocess
import platform
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QDialog,
    QVBoxLayout,
    QPushButton,
    QDesktopWidget,
    QMainWindow,
    QToolButton,
    QFrame,
)


def read_names_from_file(file_path):
    """读取名单文件并返回处理后的名单列表"""
    if not os.path.exists(file_path):
        default_names = ["小明", "李华", "张四", "小五"]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(default_names))
        return default_names

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            names = f.read().splitlines()
        return [name.strip() for name in names if name.strip()]
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []


class FloatingWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.shuffled_names = []
        self.current_index = 0
        self.load_names()
        self.drag_pos = QPoint()
        self.mouse_press_pos = QPoint()
        self.name_dialog = None
        self.init_ui()

    def init_ui(self):
        """初始化界面组件"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)

        self.label = QLabel("点名", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.8);
                font-family: 黑体;
                font-size: 16px;
                border-radius: 4px;
            }
        """)
        self.label.setFixedSize(50, 40)
        self.setFixedSize(50, 40)
        self.move_to_corner()

    def load_names(self):
        """加载名单并初始化洗牌队列"""
        file_path = os.path.join(os.path.dirname(__file__), "names.txt")
        self.names = read_names_from_file(file_path)
        self.reset_shuffle()

    def reset_shuffle(self):
        """执行洗牌算法重置队列"""
        self.shuffled_names = self.names.copy()
        random.shuffle(self.shuffled_names)
        self.current_index = 0

    def move_to_corner(self):
        """移动窗口到屏幕右下角"""
        screen = QDesktopWidget().availableGeometry()
        taskbar_height = 72
        x = screen.width() - self.width() - 1
        y = screen.height() - taskbar_height
        self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.mouse_press_pos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if (event.globalPos() - self.mouse_press_pos).manhattanLength() <= QApplication.startDragDistance():
                self.show_random_name()
            event.accept()

    def show_random_name(self):
        """显示随机点名结果"""
        name = self.get_next_name()
        if self.name_dialog is None:
            self.name_dialog = NameDialog(name, self)
        else:
            self.name_dialog.update_content(name)
            self.name_dialog.move_center()
        self.name_dialog.show()

    def get_next_name(self):
        """获取下一个不重复的名字"""
        if not self.shuffled_names:
            return "名单为空"

        if self.current_index >= len(self.shuffled_names):
            self.reset_shuffle()

        name = self.shuffled_names[self.current_index]
        self.current_index += 1
        return name

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class NameDialog(QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.init_ui(name)
        self.move_center()

    def init_ui(self, name):
        """初始化结果显示对话框"""
        self.setWindowTitle("随机点名结果")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("黑体", 150))

        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setFixedSize(100, 40)
        self.confirm_btn.clicked.connect(self.close)

        layout.addWidget(self.name_label)
        layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)

    def update_content(self, new_name):
        self.name_label.setText(new_name)

    def move_center(self):
        """移动窗口到屏幕中心"""
        screen = QDesktopWidget().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


class SettingsWindow(QMainWindow):
    def __init__(self, plugin_path):
        super().__init__()
        self.plugin_path = plugin_path
        self.init_ui()

    def init_ui(self):
        """初始化设置窗口"""
        self.setWindowTitle("随机点名设置")
        self.setFixedSize(400, 300)

        central_widget = QFrame()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        self.open_btn = QToolButton()
        self.open_btn.setText("打开名单文件")
        self.open_btn.clicked.connect(self.open_names_file)
        layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)

    def open_names_file(self):
        """打开名单文件进行编辑"""
        file_path = os.path.join(self.plugin_path, "names.txt")
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", file_path])
        elif platform.system() == "Darwin":
            subprocess.call(["open", file_path])


class Plugin:
    def __init__(self, cw_contexts, method):
        self.floating_window = None

    def execute(self):
        """启动插件主功能"""
        if not self.floating_window:
            self.floating_window = FloatingWindow()
        self.floating_window.show()


class Settings:
    def __init__(self, plugin_path, parent=None):
        self.window = SettingsWindow(plugin_path)

    def show(self):
        """显示设置窗口"""
        self.window.show()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())