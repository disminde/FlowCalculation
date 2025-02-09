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
            f"鉴定为堰流;\n"
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

        VIPMessage = f"下泄流量: {Qq:.2f}\n"
    else:
        result_text = (
            f"鉴定为孔流;"
            f"是否淹没: {'是' if isHoleSubmerge else '否'}\n"
            f"孔流流量系数: {holeFlowCoefficient:.2f}\n"
            f"孔流流量偏差: {Qqdelta:.2f}\n"
            f"流量偏差: {deltaQ:.2f}\n"
            f"理想闸门开高: {e0:.2f}\n"
        )

        VIPMessage = f"下泄流量: {Q:.2f}\n"

    result_text += (f""
        f"---------------------------------------\n"
        f"h (闸上实测水头): {h:.2f}\n"
        f"h1 (上下游水位差): {h1:.2f}\n"
        f"S (闸上水尺断面面积): {S:.2f}\n"
        f"v0 (闸上水尺断面平均流速): {v0:.2f}\n"
        f"H (总水头): {H:.2f}\n"
    )


    update_result_label(result_text)

    # 清空 Discharge_flow_down_the_hole 文本框，并插入 VIPMessage
    Discharge_flow_down_the_hole.delete("1.0", tk.END)  # 清空文本框
    Discharge_flow_down_the_hole.insert(tk.END, VIPMessage)  # 插入 VIPMessage

    # result_text_widget.delete("1.0", tk.END)
    # result_text_widget.insert(tk.END, result_text)

    final_result = (result_text, VIPMessage)
    return final_result

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
    text_widget = tk.Text(readme_window, wrap="word", font=("Consolas", 12),bg="#F0F0F0")
    text_widget.pack(expand=True, fill="both", padx=10, pady=10)

    # 插入 README 内容
    text_widget.insert("1.0", readme_content)
    text_widget.config(state="disabled")  # 禁止编辑

def configure_styles():
    bg_color = "#F0F0F0"
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
    style.configure("Card.TFrame", background=bg_color, borderwidth=0, relief="flat")
    style.configure("TLabel", font=("Segoe UI", 11), background=bg_color,borderwidth=0, relief="flat")
    style.configure("TButton", font=("Segoe UI", 11, "bold"), borderwidth=0, relief="flat")
    style.configure("TEntry", fieldbackground=bg_color, borderwidth=0, relief="flat")

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
    def __init__(self, master=None, text="", command=None, radius=10, bg_color="#D3D3D3", fg_color="#000000", hover_color="#1C86EE", shadow_color="#888888", width=100, height=40, **kwargs):
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

def disable_selection(event):
    return "break"

root = tk.Tk()
root.title("Water Flow Calculation\n")
root.geometry("1000x720")
root.minsize(400, 300)
configure_styles()

main_frame = ttk.Frame(root)
main_frame.pack(expand=True, fill="both", padx=20, pady=20)

# 设置主区域为三列三行布局
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=0)
main_frame.columnconfigure(2, weight=6)
main_frame.rowconfigure(0, weight=0)  # 第一行：标题及按钮
main_frame.rowconfigure(1, weight=0)  # 第二行：文件选择、配置区、输入字段
main_frame.rowconfigure(2, weight=0)  # 第三行：结果显示区

# ============ 第一行（row 0） ============
# 标题区域：放在第一行左侧两列（col 0 和 col 1 合并）
title_frame = ttk.Frame(main_frame, style="Card.TFrame")
title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
ttk.Label(title_frame,
          text="水利工程流量计算系统\nWater Flow Calculation System",
          style="Title.TLabel").pack(pady=15)

# 操作按钮区域：放在第一行第三列（col 2）
btn_frame_top = ttk.Frame(main_frame)
btn_frame_top.grid(row=0, column=2, sticky="ew", padx=10, pady=10)

# “批量处理”按钮
batch_btn = ttk.Button(btn_frame_top, text="批量处理", command=select_file)
batch_btn.pack(side="left", padx=10)
batch_btn.config(state="disabled")

# “查看使用手册”按钮
readme_btn = ttk.Button(btn_frame_top, text="查看使用手册", command=show_readme_window)
readme_btn.pack(side="left", padx=10)

# ============ 第二行（row 1） ============

config_input_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
config_input_frame.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
config_input_frame.columnconfigure(1, weight=1)

# 文件选择部分（原先在 input_card 内）
ttk.Label(config_input_frame, text="选择配置文件:").grid(row=0, column=0, sticky="w", pady=5)
file_combobox = ttk.Combobox(config_input_frame, values=load_json_files(), width=2)
file_combobox.grid(row=0, column=1, pady=10, sticky="ew")
file_combobox.bind("<<ComboboxSelected>>", lambda e: on_file_select(file_combobox.get()))

ttk.Label(config_input_frame, text="当前配置详情", font=("Segoe UI", 12, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

config_text = tk.Text(config_input_frame, wrap=tk.WORD, height=25, font=("Consolas", 9), bg="#F0F0F0",width=2)
config_text.grid(row=2, column=0, columnspan=2, sticky="nsew")
config_text.insert(tk.END, "请选择配置文件查看详细信息")
config_text.config(state="disabled")

config_text.bind("<Button-1>", disable_selection)  # 禁止鼠标点击
config_text.bind("<B1-Motion>", disable_selection)  # 禁止鼠标拖动选中
config_text.bind("<Control-a>", disable_selection)  # 禁止 Ctrl + A 选中全部
config_text.bind("<Key>", disable_selection)  # 禁止键盘输入

# 右侧单元格（col 2）：输入字段区域（移动自原 input_card 内除文件选择部分之外的内容）
input_fields_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
input_fields_frame.grid(row=1, column=2, sticky="nsew", padx=10)
input_fields_frame.columnconfigure(1, weight=1)

style = ttk.Style()
style.configure("White.TEntry", fieldbackground="white")

# 输入字段

entry_H1 = ttk.Entry(input_fields_frame, style="White.TEntry")
entry_H2 = ttk.Entry(input_fields_frame, style="White.TEntry")
entry_Qt = ttk.Entry(input_fields_frame, style="White.TEntry")
entry_n = ttk.Entry(input_fields_frame, style="White.TEntry")
entry_e = ttk.Entry(input_fields_frame, style="White.TEntry")

# 使用一个行号计数器来依次排布各组件
current_row = 1

# H1 (上游水头)
ttk.Label(input_fields_frame, text="H1 (上游水头):").grid(row=current_row, column=0, sticky="w", pady=5)
entry_H1.grid(row=current_row, column=1, sticky="ew", pady=5)
entry_H1.config(state="disabled")
current_row += 1

# H2 (下游水头)
ttk.Label(input_fields_frame, text="H2 (下游水头):").grid(row=current_row, column=0, sticky="w", pady=5)
entry_H2.grid(row=current_row, column=1, sticky="ew", pady=5)
entry_H2.config(state="disabled")
current_row += 1

# 在 Qt 输入栏上方添加注释 "输入预期流量" 及一条横线分割
ttk.Label(input_fields_frame,
          text="输入预期流量",
          font=("Arial", 10, "italic"),
          foreground="gray").grid(row=current_row, column=0, columnspan=2, sticky="w", pady=(10, 0))
current_row += 1
ttk.Separator(input_fields_frame, orient="horizontal").grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
current_row += 1

# Qt (调试目标)
ttk.Label(input_fields_frame, text="Qt (调试目标):").grid(row=current_row, column=0, sticky="w", pady=5)
entry_Qt.grid(row=current_row, column=1, sticky="ew", pady=5)
entry_Qt.config(state="disabled")
current_row += 1

# 在 n 和 e 输入栏上方添加注释 "输入参数进行计算，可尝试不同组合" 及横线分割
ttk.Label(input_fields_frame,
          text="输入参数进行计算，可尝试不同组合",
          font=("Arial", 10, "italic"),
          foreground="gray").grid(row=current_row, column=0, columnspan=2, sticky="w", pady=(10, 0))
current_row += 1
ttk.Separator(input_fields_frame, orient="horizontal").grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
current_row += 1

# n (开启孔数)
ttk.Label(input_fields_frame, text="n (开启孔数):").grid(row=current_row, column=0, sticky="w", pady=5)
entry_n.grid(row=current_row, column=1, sticky="ew", pady=5)
entry_n.config(state="disabled")
current_row += 1

# e (开启高度)
ttk.Label(input_fields_frame, text="e (开启高度):").grid(row=current_row, column=0, sticky="w", pady=5)
entry_e.grid(row=current_row, column=1, sticky="ew", pady=5)
entry_e.config(state="disabled")
current_row += 1

# 开始计算按钮
calculate_btn = CanvasButton(input_fields_frame, text="开始试算", command=calculate,
                             width=360, height=45, bg_color="#2A73FF")
calculate_btn.grid(row=current_row, column=0, columnspan=2, pady=20)
current_row += 1

# 显示计算结果的文本框
Discharge_flow_down_the_hole = tk.Text(input_fields_frame, wrap=tk.WORD,
                                         font=("Consolas", 20), bg="#F0F0F0",
                                         height=2, width=10)
Discharge_flow_down_the_hole.grid(row=current_row, column=0, columnspan=2, sticky="nsew", padx=(0, 10))
Discharge_flow_down_the_hole.tag_configure('highlight', font=("黑体", 20, "bold"), foreground="#2A73FF")


# fields = [
#     ("H1 (上游水头):", entry_H1 := ttk.Entry(input_fields_frame, style="White.TEntry")),
#     ("H2 (下游水头):", entry_H2 := ttk.Entry(input_fields_frame, style="White.TEntry")),
#     ("Qt (调试目标):", entry_Qt := ttk.Entry(input_fields_frame, style="White.TEntry")),
#     ("n (开启孔数):", entry_n := ttk.Entry(input_fields_frame, style="White.TEntry")),
#     ("e (开启高度):", entry_e := ttk.Entry(input_fields_frame, style="White.TEntry"))
# ]
#
# for idx, (label_text, entry) in enumerate(fields,start=1):
#     ttk.Label(input_fields_frame, text=label_text).grid(row=idx, column=0, sticky="w", pady=5)
#     entry.grid(row=idx, column=1, sticky="ew", pady=5)
#     entry.config(state="disabled")
#
# calculate_btn = CanvasButton(input_fields_frame, text="开始计算", command=calculate,
#                              width=360, height=45, bg_color="#2A73FF")
# calculate_btn.grid(row=6, column=0,columnspan=2, pady=20)
#
# Discharge_flow_down_the_hole = tk.Text(input_fields_frame, wrap=tk.WORD, font=("Consolas", 20), bg="#F0F0F0",height=2,width=10)
# Discharge_flow_down_the_hole.grid(row=7, column=0,columnspan=2, sticky="nsew", padx=(0, 10))
# Discharge_flow_down_the_hole.tag_configure('highlight', font=("黑体", 20, "bold"), foreground="#2A73FF")

# ============ 第三行（row 2） ============

# 结果显示区：放在第三行第三列（col 2），内部将 flow_text_widget 与 result_text_widget 改为左右排列
result_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
result_frame.grid(row=2, column=2, sticky="nsew", pady=10, padx=10)
result_frame.columnconfigure(0, weight=1)
result_frame.columnconfigure(1, weight=1)
result_frame.rowconfigure(1, weight=1)

flow_label = ttk.Label(result_frame, text="流量计算结果", font=("微软雅黑", 12, "bold"))
flow_label.grid(row=0, column=0, sticky="ew", pady=(5, 2))

flow_text_widget = tk.Text(result_frame, wrap=tk.WORD, font=("Consolas", 10), bg="#F0F0F0",height=5,width=5)
flow_text_widget.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
flow_text_widget.tag_configure('highlight', font=("黑体", 10, "bold"), foreground="#2A73FF")

result_label = ttk.Label(result_frame, text="详细计算结果", font=("微软雅黑", 12, "bold"))
result_label.grid(row=0, column=1, sticky="ew", pady=(5, 2))

result_text_widget = tk.Text(result_frame, wrap=tk.WORD, font=("Consolas", 10), bg="#F0F0F0",height=5,width=5)
result_text_widget.grid(row=1, column=1, sticky="nsew")
result_text_widget.tag_configure('highlight', font=("黑体", 10, "bold"), foreground="#2A73FF")

flow_text_widget.bind("<Button-1>", disable_selection)  # 禁止鼠标点击
flow_text_widget.bind("<B1-Motion>", disable_selection)  # 禁止鼠标拖动选中
flow_text_widget.bind("<Control-a>", disable_selection)  # 禁止 Ctrl + A 选中全部
flow_text_widget.bind("<Key>", disable_selection)  # 禁止键盘输入

result_text_widget.bind("<Button-1>", disable_selection)  # 禁止鼠标点击
result_text_widget.bind("<B1-Motion>", disable_selection)  # 禁止鼠标拖动选中
result_text_widget.bind("<Control-a>", disable_selection)  # 禁止 Ctrl + A 选中全部
result_text_widget.bind("<Key>", disable_selection)  # 禁止键盘输入

footer_label = ttk.Label(root, text="版权所有 © disminder", font=("Arial", 8))
footer_label.place(relx=1.0, rely=1.0, anchor="se")

root.mainloop()