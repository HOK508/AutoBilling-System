import tkinter as tk
from tkinter import messagebox, ttk
import csv
import os
import datetime
import matplotlib.pyplot as plt
import qrcode
import base64
import requests
from dotenv import load_dotenv
from matplotlib.font_manager import FontProperties
from collections import defaultdict
import matplotlib.dates as mdates

# === 加载环境变量 ===
load_dotenv()

# === 路径与配置 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'expense_data.csv')
REPORT_FILE = os.path.join(BASE_DIR, 'report.png')
FONT_PATH = os.path.join(BASE_DIR, 'NotoSansCJKsc-Regular.otf')

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === 初始化 CSV 文件 ===
def init_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '金额', '类别', '备注'])

# === 保存支出 ===
def save_expense(date, amount, category, note):
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, amount, category, note])

# === 读取记录 ===
def read_expenses():
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            records = list(reader)
    return records

# === 上传文件到 GitHub ===
def upload_file_to_github(filepath):
    if not GITHUB_USERNAME or not REPO_NAME or not GITHUB_TOKEN:
        messagebox.showerror("错误", "GitHub 配置不完整，请检查 .env 文件")
        return None

    if not os.path.exists(filepath):
        messagebox.showerror("错误", f"文件不存在：{filepath}")
        return None

    filename = os.path.basename(filepath)
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{filename}"

    with open(filepath, 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # 获取 SHA（用于更新）
    sha = None
    res = requests.get(api_url, headers=headers)
    if res.status_code == 200:
        sha = res.json().get('sha')

    data = {
        "message": f"Upload {filename}",
        "content": content,
    }
    if sha:
        data["sha"] = sha

    res = requests.put(api_url, json=data, headers=headers)
    if res.status_code in [200, 201]:
        return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/{filename}"
    else:
        messagebox.showerror("上传失败", f"{res.status_code}: {res.text}")
        return None

def generate_and_upload_report():

    # 数据准备
    category_totals = defaultdict(float)
    daily_totals = defaultdict(float)
    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")

    monthly_total = 0.0
    today_total = 0.0

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date = datetime.datetime.strptime(row['日期'], '%Y-%m-%d').date()
                amount = float(row['金额'])
                category = row['类别']

                if date == today:
                    category_totals[category] += amount
                daily_totals[date] += amount

                if date.strftime("%Y-%m") == current_month:
                    monthly_total += amount
                if date == today:
                    today_total += amount
            except Exception as e:
                print("数据处理错误：", e)

    if not category_totals:
        messagebox.showinfo("提示", "没有数据可生成图表")
        return

    # 准备字体
    font_prop = FontProperties(fname=FONT_PATH)

    # 创建图形（1行2列，增宽，调节间距）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.subplots_adjust(wspace=0.4)

    # 饼图：标签在圆外，百分比在圆内
    # 准备标签（显示在圆外）
    labels = [f"{cat} {amt:.0f}元" for cat, amt in category_totals.items()]
    total_amount = sum(category_totals.values())

    # 显示百分比在扇形内
    def autopct_format(pct):
        return f"{pct:.1f}%"

    ax1.pie(
        category_totals.values(),
        labels=labels,
        autopct=autopct_format,
        startangle=90,
        labeldistance=1.15,  # 标签放在扇形外
        textprops={'fontproperties': font_prop}
    )
    ax1.set_title("支出分类图", fontproperties=font_prop)



    # 折线图部分
    sorted_dates = sorted(daily_totals.keys())
    amounts = [daily_totals[date] for date in sorted_dates]
    ax2.plot(sorted_dates, amounts, marker='o', color='tab:blue')
    for x, y in zip(sorted_dates, amounts):
        ax2.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 8),
                     ha='center', fontproperties=font_prop, fontsize=9)

    ax2.set_title("每日支出趋势", fontproperties=font_prop)
    ax2.set_xlabel("日期", fontproperties=font_prop)
    ax2.set_ylabel("金额（元）", fontproperties=font_prop)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.tick_params(axis='x', rotation=45)

    # 图像上添加总结文本
    summary_text = f"本月总支出：{monthly_total:.2f} 元\n今日支出：{today_total:.2f} 元"
    fig.text(0.5, 0.02, summary_text, ha='center', fontsize=12, fontproperties=font_prop, color='darkred')

    # 调整布局并保存
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(REPORT_FILE)
    plt.close()

    # 上传到 GitHub 并生成二维码
    url = upload_file_to_github(REPORT_FILE)
    if url:
        messagebox.showinfo("图表生成完成", f"报告已上传\n{url}")
        generate_qr(url)

# === 生成二维码 ===
def generate_qr(link):
    img = qrcode.make(link)
    img.save(os.path.join(BASE_DIR, "share_qr.png"))
    messagebox.showinfo("二维码已生成", "二维码保存为 share_qr.png")

# === GUI ===
DATA_FILE = os.path.join(os.path.dirname(__file__), 'expense_data.csv')

def save_expense(date, amount, category, note):
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, amount, category, note])

def read_expenses():
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            records = list(reader)
    return records

class ExpenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("个人记账本")
        self.root.geometry("600x500")

        # 初始化分类集合
        self.custom_categories = {"餐饮", "交通", "购物", "其他"}

        self.build_ui()

    def generate_daily_trend_chart(self):
        from collections import defaultdict
        import matplotlib.dates as mdates

        # 汇总每日支出
        daily_totals = defaultdict(float)
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = datetime.datetime.strptime(row['日期'], "%Y-%m-%d").date()
                    amount = float(row['金额'])
                    daily_totals[date] += amount
                except Exception:
                    continue  # 跳过格式错误行

        if not daily_totals:
            messagebox.showinfo("提示", "没有数据可生成趋势图")
            return

        # 排序数据
        dates = sorted(daily_totals.keys())
        amounts = [daily_totals[d] for d in dates]

        # 绘图
        plt.figure(figsize=(8, 4))
        font_prop = FontProperties(fname=FONT_PATH)
        plt.plot(dates, amounts, marker='o', linestyle='-', color='blue')
        plt.title("每日支出趋势图", fontproperties=font_prop)
        plt.xlabel("日期", fontproperties=font_prop)
        plt.ylabel("支出金额（元）", fontproperties=font_prop)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.gcf().autofmt_xdate()
        plt.grid(True)

        trend_path = os.path.join(BASE_DIR, 'daily_trend.png')
        plt.savefig(trend_path)
        plt.close()

        # 上传并生成二维码
        url = upload_file_to_github(trend_path)
        if url:
            messagebox.showinfo("趋势图已生成", f"链接：{url}")
            generate_qr(url)

    def build_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        from tkcalendar import DateEntry

        # 日期选择器（禁止选择未来日期）
        tk.Label(frame, text="日期:").grid(row=0, column=0)
        self.date_entry = DateEntry(
            frame,
            date_pattern="yyyy-mm-dd",
            maxdate=datetime.date.today()  # 限制最大可选日期为今天
        )
        self.date_entry.set_date(datetime.date.today())
        self.date_entry.grid(row=0, column=1)

        # 金额
        tk.Label(frame, text="金额:").grid(row=1, column=0)
        self.amount_entry = tk.Entry(frame)
        self.amount_entry.grid(row=1, column=1)

        # 类别（下拉）
        tk.Label(frame, text="类别:").grid(row=2, column=0)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=sorted(self.custom_categories),
            state="readonly"
        )
        self.category_combo.set("餐饮")
        self.category_combo.grid(row=2, column=1)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        # “其他类别”输入（默认不显示）
        self.other_category_label = tk.Label(frame, text="其他类别:")
        self.other_category_entry = tk.Entry(frame)

        # 备注
        tk.Label(frame, text="备注:").grid(row=4, column=0)
        self.note_entry = tk.Entry(frame)
        self.note_entry.grid(row=4, column=1)

        # 按钮
        tk.Button(self.root, text="添加支出", command=self.add_record).pack(pady=5)
        tk.Button(self.root, text="查看记录", command=self.show_records).pack(pady=5)
        tk.Button(self.root, text="生成图表并上传", command=generate_and_upload_report).pack(pady=5)

        # 表格显示
        self.tree = ttk.Treeview(self.root, columns=('日期', '金额', '类别', '备注'), show='headings')
        for col in ('日期', '金额', '类别', '备注'):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

    def on_category_change(self, event=None):
        if self.category_var.get() == "其他":
            self.other_category_label.grid(row=3, column=0)
            self.other_category_entry.grid(row=3, column=1)
        else:
            self.other_category_label.grid_forget()
            self.other_category_entry.grid_forget()

    def add_record(self):
        date = self.date_entry.get()
        amount = self.amount_entry.get()
        note = self.note_entry.get()

        # 处理分类
        if self.category_var.get() == "其他":
            category = self.other_category_entry.get().strip()
            if not category:
                messagebox.showerror("错误", "请填写自定义类别")
                return
            if category not in self.custom_categories:
                self.custom_categories.add(category)
                self.category_combo['values'] = sorted(self.custom_categories)
        else:
            category = self.category_var.get()

        try:
            float(amount)
            save_expense(date, amount, category, note)
            messagebox.showinfo("成功", "支出已记录")
            self.clear_fields()

            # ✅ 自动生成图表并上传
            generate_and_upload_report()

        except ValueError:
            messagebox.showerror("错误", "金额必须是数字")

    def clear_fields(self):
        self.amount_entry.delete(0, tk.END)
        self.note_entry.delete(0, tk.END)
        self.category_combo.set("餐饮")
        self.other_category_entry.delete(0, tk.END)
        self.on_category_change()  # 重置“其他”输入框显示状态

    def show_records(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in read_expenses():
            self.tree.insert('', tk.END, values=row)

# === 入口 ===
if __name__ == '__main__':
    init_file()
    root = tk.Tk()
    app = ExpenseApp(root)
    root.mainloop()