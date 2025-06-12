# 📒 个人记账系统（Auto Billing System）

一个基于 Python 和 Tkinter 的桌面记账应用，支持支出录入、历史记录查看、图表可视化与 GitHub 云端同步分享。适合日常财务管理和学习实践使用。

![screenshot](https://your-image-link-if-uploaded.png)

---

## ✨ 功能特色

- ✅ 图形化界面，支持中文，操作直观
- 🗓 支持日期、金额、类别、备注四项信息记录
- 🔍 查看历史记录（CSV 存储）
- 📊 生成支出分类饼图 & 每日支出趋势图
- ☁️ 上传图表到 GitHub，自动生成公开访问链接
- 📱 生成二维码，扫码查看图表报告

---

## 📦 技术栈

- Python 3.x
- Tkinter（GUI 界面）
- Matplotlib（图表绘制）
- qrcode（二维码生成）
- requests（GitHub API 调用）
- dotenv（环境变量配置）


---

## 🚀 使用方法

### 1️⃣ 安装依赖以及启动

```bash
pip install matplotlib qrcode python-dotenv tk tkcalendar requests

python auto_billing.py
