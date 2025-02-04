import os
import random
import subprocess
import platform
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QMouseEvent, QColor, QPainter
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
    QHBoxLayout,
)


def read_names_from_file(file_path):
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
        self.names = read_names_from_file(os.path.join(os.path.dirname(__file__), "names.txt"))
        self.last_name = None
        self.drag_pos = QPoint()
        self.mouse_press_pos = QPoint()
        self.mouse_move_pos = QPoint()
        self.name_dialog = None  # 用于保存NameDialog实例
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)

        self.label = QLabel("随机点名", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            """
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.8);
                font-family: 黑体;
                font-size: 16px;
                border-radius: 4px;
            }
            """
        )
        self.label.setFixedSize(100, 40)
        self.setFixedSize(100, 40)

        self.move_to_corner()

    def move_to_corner(self):
        screen = QDesktopWidget().availableGeometry()
        taskbar_height = 72
        x = screen.width() - self.width()
        y = screen.height() - taskbar_height
        self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.mouse_press_pos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            move_distance = (event.globalPos() - self.mouse_press_pos).manhattanLength()
            if move_distance > QApplication.startDragDistance():
                self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            move_distance = (event.globalPos() - self.mouse_press_pos).manhattanLength()
            if move_distance <= QApplication.startDragDistance():
                self.show_random_name()
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    def show_random_name(self):
        name = self.get_random_name()
        if self.name_dialog is None:
            self.name_dialog = NameDialog(name, self)
        else:
            self.name_dialog.update_content(name)
            # 确保窗口居中显示
            screen = QDesktopWidget().availableGeometry()
            x = (screen.width() - self.name_dialog.width()) // 2
            y = (screen.height() - self.name_dialog.height()) // 2
            self.name_dialog.move(x, y)
        self.name_dialog.show()

    def get_random_name(self):
        if not self.names:
            return "名单为空"
        if len(self.names) == 1:
            return self.names[0]
        while True:
            name = random.choice(self.names)
            if name != self.last_name:
                self.last_name = name
                return name


class NameDialog(QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" 随机点名结果")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color:  white;")

        # 将窗口居中显示
        screen = QDesktopWidget().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        layout = QVBoxLayout(self)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont(" 黑体", 150))

        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setFixedSize(100, 40)
        self.confirm_btn.clicked.connect(self.close)

        layout.addWidget(self.name_label)
        layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)

    def update_content(self, new_name):
        self.name_label.setText(new_name)


class SettingsWindow(QMainWindow):
    def __init__(self, plugin_path):
        super().__init__()
        self.plugin_path = plugin_path
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(" 随机点名设置")
        self.setFixedSize(400, 300)

        central_widget = QFrame()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        self.open_btn = QToolButton()
        self.open_btn.setText(" 打开名单文件")
        self.open_btn.clicked.connect(self.open_names_file)
        layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)

    def open_names_file(self):
        file_path = os.path.join(self.plugin_path, "names.txt")
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", file_path])
        elif platform.system() == "Darwin":
            subprocess.call(["open", file_path])


class Plugin:
    def __init__(self, cw_contexts, method):
        self.cw_contexts = cw_contexts
        self.method = method
        self.floating_window = None

    def execute(self):
        self.floating_window = FloatingWindow()
        self.floating_window.show()


class Settings:
    def __init__(self, plugin_path, parent=None):
        self.window = SettingsWindow(plugin_path)

    def show(self):
        self.window.show()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # 测试漂浮窗口
    floating = FloatingWindow()
    floating.show()

    # 测试设置窗口
    # settings = SettingsWindow(os.path.dirname(__file__)) 
    # settings.show() 

    sys.exit(app.exec_()) 