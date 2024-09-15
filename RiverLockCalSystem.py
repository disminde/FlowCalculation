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
    flow_rates_text_widget.delete("1.0", tk.END)

    lines = flow_rates_text.split('\n')
    for line in lines:
        if "堰流下泄流量" in line or "孔流下泄流量" in line:
            # result_text_widget.insert(tk.END, line + '\n', 'large_font')
            flow_rates_text_widget.insert(tk.END, line+'\n', 'large_font')
        else:
            flow_rates_text_widget.insert(tk.END, line + '\n')

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
    calculate_button.config(state='normal')
    batch_process_button.config(state='normal')

root = tk.Tk()
root.title("Water Flow Calculation\n@disminder-v0.0.5")

large_font = font.Font(family="Arial", size=24, weight="bold")

style = ttk.Style()
style.configure("TFrame", background="#f0f0f0")
style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
style.configure("TButton", background="#4CAF50", foreground="black", font=("Arial", 10, "bold"))
style.map("TButton", background=[("active", "#45a049")])

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

title_label = ttk.Label(frame, text="Water Flow Calculation\n水利流量计算工具", font=("Arial", 16, "bold"))
title_label.grid(column=1, row=0, columnspan=2, pady=10)

ttk.Label(frame, text="Select JSON File:").grid(column=1, row=1, sticky=tk.W)
json_files = load_json_files()
file_combobox = ttk.Combobox(frame, values=json_files)
file_combobox.grid(column=2, row=1, sticky=(tk.W, tk.E))
file_combobox.bind("<<ComboboxSelected>>", on_file_select)

input_frame = ttk.Frame(frame, padding="10")
input_frame.grid(column=1, row=2, columnspan=2, pady=10)

ttk.Label(input_frame, text="H1:").grid(column=1, row=0, sticky=tk.W)
entry_H1 = ttk.Entry(input_frame, state='disabled')
entry_H1.grid(column=2, row=0, sticky=(tk.W, tk.E))

ttk.Label(input_frame, text="H2:").grid(column=1, row=1, sticky=tk.W)
entry_H2 = ttk.Entry(input_frame, state='disabled')
entry_H2.grid(column=2, row=1, sticky=(tk.W, tk.E))

ttk.Label(input_frame, text="Qt:").grid(column=1, row=2, sticky=tk.W)
entry_Qt = ttk.Entry(input_frame, state='disabled')
entry_Qt.grid(column=2, row=2, sticky=(tk.W, tk.E))

ttk.Label(input_frame, text="n:").grid(column=1, row=3, sticky=tk.W)
entry_n = ttk.Entry(input_frame, state='disabled')
entry_n.grid(column=2, row=3, sticky=(tk.W, tk.E))

ttk.Label(input_frame, text="e:").grid(column=1, row=4, sticky=tk.W)
entry_e = ttk.Entry(input_frame, state='disabled')
entry_e.grid(column=2, row=4, sticky=(tk.W, tk.E))

batch_process_button = ttk.Button(input_frame, text="Select File to Batch Process", command=select_file, state='disabled')
batch_process_button.grid(column=3, row=0, rowspan=5, padx=5, ipady=40)

calculate_button = ttk.Button(frame, text="Calculate", command=calculate, state='disabled')
calculate_button.grid(column=1, row=3, columnspan=2, pady=10)

result_frame = ttk.Frame(frame, padding="10")
result_frame.grid(column=1, row=4, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

flow_rates_text_widget = tk.Text(result_frame, wrap="word", width=50, height=5)
flow_rates_text_widget.grid(column=1, row=0, sticky=(tk.W, tk.E))

result_text_widget = tk.Text(result_frame, wrap="word", width=50, height=20)
result_text_widget.grid(column=1, row=1, sticky=(tk.W, tk.E))

result_text_widget.tag_configure('large_font', font=large_font)
flow_rates_text_widget.tag_configure('large_font', font=large_font)

config_frame = ttk.Frame(frame, padding="10")
config_frame.grid(column=3, row=0, rowspan=5, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))

config_canvas = tk.Canvas(config_frame, background="#ffffff")
config_scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=config_canvas.yview)
config_scrollable_frame = ttk.Frame(config_canvas, padding="5", relief="solid")

config_scrollable_frame.bind(
    "<Configure>",
    lambda e: (config_canvas.configure(
        scrollregion=config_canvas.bbox("all")
    ), config_canvas.itemconfig("frame", width=config_canvas.winfo_width()))
)

config_canvas.create_window((0, 0), window=config_scrollable_frame, anchor="nw", tags="frame")
config_canvas.configure(yscrollcommand=config_scrollbar.set)

config_info_label = ttk.Label(config_scrollable_frame, text="配置文件信息：", anchor="nw", justify="left", font=("Arial", 12, "bold"))
config_info_label.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

config_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
config_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

config_label = ttk.Label(config_scrollable_frame, text="", anchor="nw", justify="left")
config_label.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S))

frame.rowconfigure(0, weight=1)
frame.columnconfigure(3, weight=1)
config_frame.rowconfigure(0, weight=1)
config_frame.columnconfigure(0, weight=1)

root.mainloop()