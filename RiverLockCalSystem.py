#last update:2024-8-11
#@disminder
#v0.0.5
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from tkinter import messagebox
import math
import json
import os
import csv
import math


def load_json_files():
    json_files = [f for f in os.listdir() if f.endswith('.json')]
    return json_files

def update_result_label(result_text):
    result_text_widget.delete("1.0", tk.END)

    lines = result_text.split('\n')
    for line in lines:
        if "堰流下泄流量" in line or "孔流下泄流量" in line:
            result_text_widget.insert(tk.END, line + '\n', 'large_font')
        else:
            result_text_widget.insert(tk.END, line + '\n')

def update_state_label(flow_rates_text):
    flow_text_widget.delete("1.0", tk.END)

    lines = flow_rates_text.split('\n')
    for line in lines:
        if "堰流下泄流量" in line or "孔流下泄流量" in line:
            # result_text_widget.insert(tk.END, line + '\n', 'large_font')
            flow_text_widget.insert(tk.END, line+'\n', 'large_font')
        else:
            flow_text_widget.insert(tk.END, line + '\n')

def load_config_data(file_name):
    with open(file_name, 'r') as file:
        json_str = file.read()
    config_data = json.loads(json_str)
    config_data['data'] = {float(k): v for k, v in config_data['data'].items()}
    if isinstance(config_data['C0_map'], dict):
        config_data['C0_map'] = {float(k): v for k, v in config_data['C0_map'].items()}
    if isinstance(config_data['holeSubmergeCoefficient'], dict):
        config_data['holeSubmergeCoefficient'] = {float(k): v for k, v in config_data['holeSubmergeCoefficient'].items()}
    return config_data

def update_C0_from_json(n):
    global config_data
    C0_map = config_data['C0_map']
    if isinstance(C0_map, (int, float)):
        return C0_map
    elif isinstance(C0_map, dict):
        if n in C0_map:
            return C0_map[n]
        else:
            return 1.00

def find_closest_keys(data, H1):
    keys = sorted(data.keys())
    for i in range(len(keys) - 1):
        if keys[i] <= H1 <= keys[i + 1]:
            return keys[i + 1], keys[i + 2]
    return None, None

def linear_interpolation(data, H1):
    x1, x2 = find_closest_keys(data, H1)
    if x1 is None or x2 is None:
        return None
    y1, y2 = data[x1], data[x2]
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    result = slope * H1 + intercept
    return result

def update_holeSubmergeCoefficient_from_json(DH):
    global holeSubmergeCoefficient
    holeSubmergeCoefficient = config_data['holeSubmergeCoefficient']
    if isinstance(holeSubmergeCoefficient, (int, float)):
        return holeSubmergeCoefficient
    elif isinstance(holeSubmergeCoefficient, dict):
        if DH in holeSubmergeCoefficient:
            return holeSubmergeCoefficient[DH]
        else:
            return linear_interpolation(holeSubmergeCoefficient, DH)


def calculate():
    global config_data
    C0 = None
    Hb = config_data['Hb']
    g = config_data['g']
    b = config_data['b']
    alpha = config_data['alpha']
    holeSubmergeCoefficient = None
    data = config_data['data']

    H1 = float(entry_H1.get())
    H2 = float(entry_H2.get())
    Qt = float(entry_Qt.get())
    n = float(entry_n.get())
    e = float(entry_e.get())

    C0 = update_C0_from_json(n)

    h = H1 - Hb
    h1 = H1 - H2
    S = linear_interpolation(data, H1)
    v0 = Qt / S
    H = h + ((alpha * pow(v0, 2)) / (2 * g))
    DH = h1 / H

    flowstate = 1 if e / H >= 0.65 else 0

    holeFlowCoefficient = 0.531 * (pow((e / H), -0.139))
    isHoleSubmerge = 1 if H2 - (Hb + e) > 0 else 0
    holeSubmergeCoefficient = update_holeSubmergeCoefficient_from_json(DH)

    Q = holeFlowCoefficient * n * b * e * math.sqrt(2 * g * H)
    deltaQ = Q - Qt
    e0 = Qt / (holeFlowCoefficient * n * b * math.sqrt(2 * g * H))

    isWeirSubmerge = 1 if (H2 - Hb) / H > 0.8 else 0

    Qq = C0 * n * b * holeSubmergeCoefficient * pow(H, 1.5)
    Qqdelta = Qq - S

    if flowstate == 1:
        flow_rates_text = (
            f"鉴定为堰流;"
            f"是否淹没: {'是' if isWeirSubmerge else '否'}\n"
            f"堰流下泄流量: {Qq:.2f}\n"
            f"理想闸门开高: {e0:.2f}\n"
        )

    else:
        flow_rates_text = (
            f"鉴定为孔流;"
            f"是否淹没: {'是' if isHoleSubmerge else '否'}\n"
            f"孔流下泄流量: {Q:.2f}\n"
            f"理想闸门开高: {e0:.2f}\n"
        )

    update_state_label(flow_rates_text)

    # flow_rates_text_widget.delete("1.0", tk.END)
    # flow_rates_text_widget.insert(tk.END, flow_rates_text)

    if flowstate == 1:
        result_text = (
            f"鉴定为堰流;"
            f"堰流下泄流量: {Qq:.2f}\n"
            f"是否淹没: {'是' if isWeirSubmerge else '否'}\n"
            f"堰流流量系数: {C0:.2f}\n"
            f"堰流流量偏差: {deltaQ:.2f}\n"
            f"流量偏差: {deltaQ:.2f}\n"
            f"理想闸门开高: {e0:.2f}\n"
        )
    else:
        result_text = (
            f"鉴定为孔流;"
            f"是否淹没: {'是' if isHoleSubmerge else '否'}\n"
            f"孔流流量系数: {holeFlowCoefficient:.2f}\n"
            f"孔流流量偏差: {Qqdelta:.2f}\n"
            f"流量偏差: {deltaQ:.2f}\n"
            f"理想闸门开高: {e0:.2f}\n"
        )

    result_text += (
        f"---------------------------------------\n"
        f"h (闸上实测水头): {h:.2f}\n"
        f"h1 (上下游水位差): {h1:.2f}\n"
        f"S (闸上水尺断面面积): {S:.2f}\n"
        f"v0 (闸上水尺断面平均流速): {v0:.2f}\n"
        f"H (总水头): {H:.2f}\n"
    )

    update_result_label(result_text)
    # result_text_widget.delete("1.0", tk.END)
    # result_text_widget.insert(tk.END, result_text)
    return result_text

def on_file_select(event):
    selected_file = file_combobox.get()
    global config_data
    config_data = load_config_data(selected_file)
    display_config_data(config_data)
    if selected_file:
        enable_inputs()

def display_config_data(config_data):
    config_text = json.dumps(config_data, indent=4)
    config_label.config(text=config_text)

def batch_process(file_path):
    with open(file_path, 'r') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # 读取并保存标题行
        data_sets = list(reader)

    with open(file_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)  # 写入标题行

        for data_set in data_sets:
            if len(data_set) > 5:
                writer.writerow(data_set)  # 直接写入不处理的数据行
                continue

            H1 = float(data_set[0])
            H2 = float(data_set[1])
            Qt = float(data_set[2])
            n = float(data_set[3])
            e = float(data_set[4])

            # 计算过程
            Hb = config_data['Hb']
            g = config_data['g']
            b = config_data['b']
            alpha = config_data['alpha']
            data = config_data['data']

            C0 = update_C0_from_json(n)

            h = H1 - Hb
            h1 = H1 - H2
            S = linear_interpolation(data, H1)
            v0 = Qt / S
            H = h + ((alpha * pow(v0, 2)) / (2 * g))
            DH = h1 / H

            flowstate = 1 if e / H >= 0.65 else 0

            holeFlowCoefficient = 0.531 * (pow((e / H), -0.139))
            isHoleSubmerge = 1 if H2 - (Hb + e) > 0 else 0
            holeSubmergeCoefficient = update_holeSubmergeCoefficient_from_json(DH)

            Q = holeFlowCoefficient * n * b * e * math.sqrt(2 * g * H)
            deltaQ = Q - Qt
            e0 = Qt / (holeFlowCoefficient * n * b * math.sqrt(2 * g * H))

            isWeirSubmerge = 1 if (H2 - Hb) / H > 0.8 else 0

            Qq = C0 * n * b * holeSubmergeCoefficient * pow(H, 1.5)
            Qqdelta = Qq - S

            result_data = [
                f"{h:.2f}", f"{h1:.2f}", f"{S:.2f}", f"{v0:.2f}", f"{H:.2f}"
            ]
            if flowstate == 1:
                result_data.extend([
                    "堰流", f"{isWeirSubmerge}", f"{Qq:.2f}", f"{C0:.2f}", f"{deltaQ:.2f}", f"{e0:.2f}"
                ])
            else:
                result_data.extend([
                    "孔流", f"{isHoleSubmerge}", f"{Q:.2f}", f"{holeFlowCoefficient:.2f}", f"{Qqdelta:.2f}", f"{e0:.2f}"
                ])

            writer.writerow(data_set + result_data)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        batch_process(file_path)
        messagebox.showinfo("完成", "Done")

def enable_inputs():
    entry_H1.config(state='normal')
    entry_H2.config(state='normal')
    entry_Qt.config(state='normal')
    entry_n.config(state='normal')
    entry_e.config(state='normal')
    calculate_btn.config(state='normal')
    batch_btn.config(state='normal')

#____________________________________________________________________________

config_data = None
holeSubmergeCoefficient = None


def show_readme_window():
    """弹出窗口，显示 readme.txt 的内容"""
    try:
        with open("readme.txt", "r", encoding="utf-8") as file:
            readme_content = file.read()
    except FileNotFoundError:
        readme_content = "未找到 readme.txt 文件！"

    # 创建新窗口
    readme_window = tk.Toplevel(root)
    readme_window.title("README 文件")
    readme_window.geometry("600x400")

    # 创建文本显示框
    text_widget = tk.Text(readme_window, wrap="word", font=("Consolas", 12))
    text_widget.pack(expand=True, fill="both", padx=10, pady=10)

    # 插入 README 内容
    text_widget.insert("1.0", readme_content)
    text_widget.config(state="disabled")  # 禁止编辑

def configure_styles():
    bg_color = "#F8F9FA"
    card_color = "#FFFFFF"
    accent_color = "#2A73FF"
    text_primary = "#2D3436"
    text_secondary = "#636E72"
    shadow_color = "#E0E0E0"

    style = ttk.Style()
    style.theme_use('clam')

    # 基础样式
    style.configure(".", background=bg_color, foreground=text_primary)
    style.configure("TFrame", background=bg_color,borderwidth=0, relief="flat")
    style.configure("Card.TFrame", background=card_color, borderwidth=0, relief="flat")
    style.configure("TLabel", font=("Segoe UI", 11), background=bg_color,borderwidth=0, relief="flat")
    style.configure("TButton", font=("Segoe UI", 11, "bold"), borderwidth=0, relief="flat")
    style.configure("TEntry", fieldbackground=card_color, borderwidth=0, relief="flat")

    # 自定义样式
    style.configure("Title.TLabel",
                    font=("Segoe UI", 24, "bold"),
                    foreground=accent_color,
                    anchor="center")

    style.configure("ResultText.TLabel",
                    font=("Consolas", 10),
                    background=card_color,
                    padding=5)

class CanvasButton(tk.Canvas):
    def __init__(self, master=None, text="", command=None, radius=10, bg_color="#1E90FF", fg_color="#000000", hover_color="#1C86EE", shadow_color="#888888", width=100, height=40, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.radius = radius
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.shadow_color = shadow_color
        self.text = text
        self.width = width
        self.height = height
        self.configure(width=width, height=height, highlightthickness=0)  # 设置 Canvas 的尺寸
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Configure>", self.resize)
        self.draw_button()

    def draw_button(self):
        self.delete("all")
        width = self.winfo_width()  # 动态获取宽度
        height = self.winfo_height()  # 动态获取高度

        # 绘制阴影
        self.create_rectangle(
            self.radius, self.radius, width, height,
            fill=self.shadow_color, outline=self.shadow_color, tags="shadow"
        )

        # 绘制圆角矩形
        self.create_round_rect(
            0, 0, width - self.radius, height - self.radius,
            radius=self.radius, fill=self.bg_color, outline=self.bg_color, tags="button"
        )

        # 添加文本
        self.create_text(
            width // 2, height // 2,
            text=self.text, fill=self.fg_color, font=font.Font(family="Segoe UI", size=12, weight="bold"), tags="text"
        )

    def create_round_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
            x1 + radius, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def on_enter(self, event):
        self.itemconfig("button", fill=self.hover_color)
        self.itemconfig("text", fill=self.fg_color)

    def on_leave(self, event):
        self.itemconfig("button", fill=self.bg_color)
        self.itemconfig("text", fill=self.fg_color)

    def on_click(self, event):
        if self.command:
            self.command()

    def resize(self, event):
        """调整 CanvasButton 的大小以填满布局单元格"""
        self.width = event.width
        self.height = event.height
        self.draw_button()

def display_config_data(config_data):
    formatted_text = json.dumps(config_data, indent=2, ensure_ascii=False)
    config_text.config(state="normal")
    config_text.delete("1.0", tk.END)
    config_text.insert(tk.END, formatted_text)
    config_text.config(state="disabled")


def enable_controls():
    entry_H1.config(state="normal")
    entry_H2.config(state="normal")
    entry_Qt.config(state="normal")
    entry_n.config(state="normal")
    entry_e.config(state="normal")
    calculate_btn.config(state="normal")
    batch_btn.config(state="normal")


root = tk.Tk()
root.title("Water Flow Calculation\n@disminder-v0.0.8")
root.geometry("2560x1440")
root.minsize(1200, 700)
configure_styles()

main_frame = ttk.Frame(root)
main_frame.pack(expand=True, fill="both", padx=20, pady=20)

# 三列布局体系
main_frame.columnconfigure(0, weight=3)  # 输入区
main_frame.columnconfigure(1, weight=1)  # 间隔
main_frame.columnconfigure(2, weight=1)  # 配置区
main_frame.rowconfigure(0, weight=0)  # 标题
main_frame.rowconfigure(1, weight=2)  # 主内容
main_frame.rowconfigure(2, weight=1)  # 结果

# 标题区
title_frame = ttk.Frame(main_frame, style="Card.TFrame")
title_frame.grid(column=0, row=0, columnspan=3, sticky="ew", pady=(0, 20))
ttk.Label(title_frame, text="水利工程流量计算系统\nWater Flow Calculation System",
          style="Title.TLabel").pack(pady=15)

# 输入卡片
input_card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
input_card.grid(column=0, row=1, sticky="nsew", padx=10)
input_card.columnconfigure(1, weight=1)

# 文件选择
ttk.Label(input_card, text="选择配置文件:").grid(row=0, column=0, sticky="w")
file_combobox = ttk.Combobox(input_card, values=load_json_files(), width=25)
file_combobox.grid(row=0, column=1, pady=10, sticky="ew")
file_combobox.bind("<<ComboboxSelected>>", lambda e: on_file_select(file_combobox.get()))

# 输入字段
fields = [
    ("H1 (上游水头):", entry_H1 := ttk.Entry(input_card)),
    ("H2 (下游水头):", entry_H2 := ttk.Entry(input_card)),
    ("Qt (调试目标):", entry_Qt := ttk.Entry(input_card)),
    ("n (开启孔数):", entry_n := ttk.Entry(input_card)),
    ("e (开启高度):", entry_e := ttk.Entry(input_card))
]

for idx, (label, entry) in enumerate(fields, start=1):
    ttk.Label(input_card, text=label).grid(row=idx, column=0, sticky="w", pady=5)
    entry.grid(row=idx, column=1, sticky="ew", pady=5)
    entry.config(state="disabled")

# 操作按钮
btn_frame = ttk.Frame(input_card)
btn_frame.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")

calculate_btn = CanvasButton(btn_frame, text="开始计算", command=calculate,
                             width=180, height=45, bg_color="#2A73FF")
calculate_btn.pack(side="left", padx=10)

batch_btn = CanvasButton(btn_frame, text="批量处理", command=select_file,
                         width=180, height=45, bg_color="#2A73FF")
batch_btn.pack(side="left", padx=10)
batch_btn.config(state="disabled")

readme_btn = ttk.Button(main_frame, text="查看使用手册", command=show_readme_window)
readme_btn.grid(column=1, row=1, padx=10, pady=10)

# 结果展示区
result_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
result_frame.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=10)

flow_text_widget = tk.Text(result_frame, wrap=tk.WORD, height=6,
                      font=("Consolas", 20), bg="white")
flow_text_widget.pack(expand=True, fill="both")
flow_text_widget.tag_configure('highlight', font=("微软雅黑", 20, "bold"), foreground="#2A73FF")

result_text_widget = tk.Text(result_frame, wrap=tk.WORD, height=12,
                      font=("Consolas", 20), bg="white")
result_text_widget.pack(expand=True, fill="both")
result_text_widget.tag_configure('highlight', font=("微软雅黑", 20, "bold"), foreground="#2A73FF")

# 配置信息区
config_card = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
config_card.grid(column=2, row=1, rowspan=2, sticky="nsew", padx=10)

ttk.Label(config_card, text="当前配置详情",
          font=("Segoe UI", 12, "bold")).pack(anchor="w")

config_text = tk.Text(config_card, wrap=tk.WORD, height=25,
                      font=("Consolas", 9), bg="white")
config_text.pack(expand=True, fill="both")
config_text.insert(tk.END, "请选择配置文件查看详细信息")
config_text.config(state="disabled")

root.mainloop()