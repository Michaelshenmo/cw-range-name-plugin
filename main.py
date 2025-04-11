import os
import random
import subprocess
import platform
import winreg

from qfluentwidgets import PrimaryPushButton, PushButton, DisplayLabel
from qframelesswindow import FramelessDialog, FramelessWindow

from .ClassWidgets.base import PluginBase, SettingsBase
from PyQt5 import uic
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QDialog,
    QVBoxLayout,
    QDesktopWidget
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
        self.apply_theme_style()

    def init_ui(self, name):
        # 在 NameDialog 的 __init__ 方法中添加：
        self.setWindowTitle("随机点名结果")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 0, 0, 0)
        self.name_label = DisplayLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("黑体", 150))

        self.confirm_btn = PushButton()
        self.confirm_btn.setText("确定")
        self.confirm_btn.setFixedSize(100, 40)
        self.confirm_btn.clicked.connect(self.close)

        layout.addWidget(self.name_label)
        layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)
        
    def apply_theme_style(self):
        """Windows专用主题检测"""
        try:
            # 访问Windows注册表获取主题信息
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
            ) as key:
                # 读取AppsUseLightTheme的值（1=浅色，0=深色）
                theme_value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                is_light_theme = theme_value == 1
        except Exception as e:
            print(f"主题检测失败，使用默认浅色: {str(e)}")
            is_light_theme = True

        # 设置对应主题样式
        if is_light_theme:
            self.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                }
                DisplayLabel {
                    color: #000000 !important;
                }
                QPushButton {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #2B2B2B;
                }
                DisplayLabel {
                    color: #FFFFFF !important;
                }
                QPushButton {
                    background-color: #404040;
                    color: #FFFFFF;
                    border: 1px solid #505050;
                    border-radius: 4px;
                }
            """)


    def update_content(self, new_name):
        self.name_label.setText(new_name)

    def move_center(self):
        """移动窗口到屏幕中心"""
        screen = QDesktopWidget().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


class Plugin(PluginBase):
    def __init__(self, cw_contexts, method):
        super().__init__(cw_contexts, method)
        self.floating_window = None

    def execute(self):
        """启动插件主功能"""
        if not self.floating_window:
            self.floating_window = FloatingWindow()
        self.floating_window.show()


class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(os.path.join(self.PATH, "settings.ui"), self)
        open_names_list = self.findChild(PrimaryPushButton, "open_names_list")
        open_names_list.clicked.connect(self.open_names_file)

    def open_names_file(self):
        """打开名单文件进行编辑"""
        file_path = os.path.join(self.PATH, "names.txt")
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", file_path])
        elif platform.system() == "Darwin":
            subprocess.call(["open", file_path])


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())
