import subprocess
import tkinter as tk
from tkinter import ttk, Toplevel
import random
import threading

from PyQt5 import uic
from qfluentwidgets import PrimaryPushButton

from .ClassWidgets.base import SettingsBase, PluginBase
import os
import platform


def read_names_from_file(file_path):
    """
    从文件中读取名字列表。
    如果文件不存在，则创建默认名字列表。
    """
    if not os.path.exists(file_path):
        default_names = ["小明", "李华", "张四", "小五"]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(default_names))
        return default_names

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            names = f.read().splitlines()
        return [name.strip() for name in names if name.strip()]
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []


class FloatingWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.names = read_names_from_file(os.path.join(os.path.dirname(__file__), "names.txt"))
        self.last_name = None  # 记录上次点名的结果

        # 设置样式
        style = ttk.Style(self)
        style.configure("TLabel", font=('黑体', 12))
        style.configure("TButton", font=('黑体', 12))

        # 无边框窗口
        self.attributes('-topmost', 'true')  # 置顶
        self.overrideredirect(True)
        self.configure(bg='black')
        self.wait_visibility(self)
        self.wm_attributes("-alpha", 0.8)

        # 绑定Esc键关闭事件
        self.bind("<KeyPress-Escape>", self.on_escape)

        # 获取屏幕尺寸
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()

        # 窗口尺寸
        window_width = 100
        window_height = 40

        # 固定任务栏高度为72像素
        self.taskbar_height = 72

        # 检测任务栏位置（默认为底部）
        taskbar_pos = self.detect_taskbar_position()

        # 计算窗口位置
        x = ws - window_width
        y = hs - window_height - self.taskbar_height

        # 确保窗口在屏幕范围内
        x = max(0, min(x, ws - window_width))
        y = max(0, min(y, hs - window_height))

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 创建标签
        self.label = ttk.Label(
            self,
            text="随机点名",
            font=('黑体', 16),
            foreground='white',
            background='black',
            anchor='center',
            width=10
        )
        self.label.pack(expand=False, fill=tk.X)

        # 初始化拖动状态
        self.draggable = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.click_threshold = 5  # 鼠标移动距离阈值，超过则视为拖动
        self.click_x = 0
        self.click_y = 0
        self.is_dragging = False
        self.is_clicking = False

        # 绑定鼠标事件
        self.bind("<Button-1>", self.on_mouse_down)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.label.bind("<Button-1>", self.on_label_click)

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def detect_taskbar_position(self):
        """
        检测任务栏的位置（示例实现）。
        """
        try:
            # 示例：默认认为任务栏在底部
            return 'bottom'
        except Exception as e:
            print(f"检测任务栏位置失败: {e}")
            return 'unknown'

    def on_mouse_down(self, event):
        """
        鼠标按下事件处理。
        """
        print("Mouse down detected.")
        self.draggable = True
        self.drag_start_x = event.x_root - self.winfo_x()
        self.drag_start_y = event.y_root - self.winfo_y()
        self.click_x = event.x_root
        self.click_y = event.y_root

        self.is_dragging = True
        self.is_clicking = False

    def on_mouse_drag(self, event):
        """
        鼠标拖动事件处理。
        """
        if self.draggable:
            new_x = event.x_root - self.drag_start_x
            new_y = event.y_root - self.drag_start_y

            # print(f"Dragging to position: {new_x}, {new_y}")
            # 补药在我的终端拉*

            ws = self.winfo_screenwidth()
            hs = self.winfo_screenheight()
            window_width = self.winfo_width()
            window_height = self.winfo_height()

            new_x = max(0, min(new_x, ws - window_width))
            new_y = max(0, min(new_y, hs - window_height))

            self.geometry(f"+{new_x}+{new_y}")

    def on_mouse_up(self, event):
        """
        鼠标释放事件处理。
        """
        print("Mouse up detected.")
        self.draggable = False
        self.is_dragging = False

        # 判断是否发生了拖动
        dx = abs(event.x_root - self.click_x)
        dy = abs(event.y_root - self.click_y)

        if dx > self.click_threshold or dy > self.click_threshold:
            print("Detected as dragging.")
            pass  # 不触发点名
        else:
            print("Detected as clicking.")
            self.is_clicking = True
            self.show_random_name(event)

    def on_label_click(self, event):
        """
        标签点击事件处理。
        """
        print("Label click detected.")
        if not self.is_dragging:
            self.show_random_name(event)

    def show_random_name(self, event):
        """
        显示随机点名结果。
        """
        if self.is_dragging or not self.is_clicking:
            return

        name = self.get_random_name()
        self.display_result(name)

        # 重置点击标志
        self.is_clicking = False

    def get_random_name(self):
        """
        获取一个与上次不同的随机名字。
        """
        if not self.names:
            return "名单为空"

        if len(self.names) == 1:
            return self.names[0]

        while True:
            name = random.choice(self.names)
            if name != self.last_name:
                self.last_name = name
                return name

    def display_result(self, name):
        """
        显示点名结果窗口。
        """
        result_window = Toplevel(self)
        result_window.title("       随机点名结果")
        result_window.geometry("600x400+500+300")
        result_window.configure(bg='white')

        label = ttk.Label(
            result_window,
            text=name,
            font=('黑体', 150),
            anchor='center'
        )
        label.pack(expand=True, fill=tk.BOTH)

        close_button = ttk.Button(
            result_window,
            text="确定",
            command=result_window.destroy
        )
        close_button.pack(pady=10)

    def on_escape(self, event):
        """
        按Esc键关闭窗口。
        """
        self.destroy()

    def on_close(self):
        """
        窗口关闭事件处理。
        """
        super().destroy()


def start_floating_window():
    """
    启动漂浮窗口。
    """
    root = tk.Tk()
    root.withdraw()

    floating_app = FloatingWindow()
    floating_app.mainloop()


class Plugin(PluginBase):
    def __init__(self, cw_contexts, method):
        super().__init__(cw_contexts, method)

    def execute(self):
        thread = threading.Thread(target=start_floating_window)
        thread.daemon = True
        thread.start()


class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(os.path.join(self.PATH, "settings.ui"), self)
        open_names_list = self.findChild(PrimaryPushButton, "open_names_list")
        open_names_list.clicked.connect(self.open_notepad)

    def open_notepad(self):
        if platform.system() == "Windows":
            os.startfile(f'{self.PATH}/names.txt')
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", f'{self.PATH}/names.txt'])
        elif platform.system() == "Darwin":
            subprocess.call(["open", f'{self.PATH}/names.txt'])