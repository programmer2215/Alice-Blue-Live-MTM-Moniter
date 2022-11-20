import pya3 as ab
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
from tkinter import messagebox as mb
import pyperclip
import threading
import csv
from datetime import datetime
import requests as r
import time
import os

time340pm = datetime.now().replace(hour=15, minute=40, second=0, microsecond=0)
time330pm = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
'''DELAY = 60000
MSG_DELAY = 900000'''

with open('alice_blue.txt') as f:
    user_id = f.readline().strip()
    api_key = f.readline().strip()
    user_name = f.readline().strip()
with open("telegram.txt") as f:
    bot_channel = f.readline().strip()
    bot_token = f.readline().strip()
alice = ab.Aliceblue(user_id=user_id,api_key=api_key)

print(alice.get_session_id())

def send_telegram_message(msg):
    if DEBUG:
        print(msg)
        return
    req = 'https://api.telegram.org/bot' + bot_token + \
                '/sendMessage?chat_id=' + bot_channel + '&parse_mode=Markdown&text=' + msg
    response = r.get(req)

root = tk.Tk()
root.title(f"MTM Moniter {user_name}")



font_1 = Font(family='Segoe UI', 
              size=18, 
              weight='bold'
              )

account_name_lab = tk.Label(root, text=user_name, font=font_1)
account_name_lab.pack(pady=10)


font_2 = Font(family='Segoe UI', 
              size=12, 
              weight='bold'
              )
font_3 = Font(family='Segoe UI', 
              size=10, 
              weight='bold'
              )

style = ttk.Style()
style.configure("Treeview", font=font_2)
style.configure("Treeview.Heading", font=font_3)
listframe = tk.Frame(root)
listframe.pack(padx=5, pady=5)
__columns = ('#1', '#2') 
tree = ttk.Treeview(listframe, columns=__columns, show='headings', selectmode='browse', height=10)
tree.column('#1', anchor=tk.CENTER)
tree.column('#2', anchor=tk.CENTER)
tree.heading('#1', text='Stock')
tree.heading('#2', text='MTM')

STOCKS = []

def copy_security():
    cur_row = tree.focus()
    pyperclip.copy(tree.item(cur_row)['values'][0])

def copy_security_rght_clck(e):
    copy_security()

def copy_row():
    cur_row = tree.focus()
    values = [str(value) for value in tree.item(cur_row)['values']]
    string = ','.join(values)
    pyperclip.copy(string)

def my_popup(e):
    right_click_menu.tk_popup(e.x_root, e.y_root)

right_click_menu = tk.Menu(tree, tearoff=False)
right_click_menu.add_command(label="Copy Row", command=copy_row)
right_click_menu.add_command(label="Copy Security", command=copy_security)

tree.bind("<Button-3>", my_popup)
root.bind('<Control-c>', copy_security_rght_clck) 

tree.tag_configure(tagname="green", foreground="#4feb34")
tree.tag_configure(tagname="red", foreground="#f03329")
tree.pack(padx=10, pady=10)

def update_report():
    with open('report_update_date.txt') as f:
        date = f.read().strip()
        now = datetime.now().strftime("%d-%m-%Y")
        if date == now:
            return
    with open('report.csv', mode='a') as f:
        f.write("{},{}".format(now, tot_mtm))
        f.write("\n")
    with open('report_update_date.txt', 'w') as f:
        f.write(now)

fin_data = []
def update():
    global tot_mtm
    tot_mtm = 0
    data = alice.get_netwise_positions()
    tree.delete(*tree.get_children())
    for i in data:
        stock_name = i['Tsym']
        mtm = float(''.join(i['MtoM'].split(',')))
        tot_mtm += mtm
        if mtm < 0:
            tag = "red"
        else:
            tag = "green"
        tree.insert("", tk.END, values=(stock_name, i['MtoM']), tags=tag)
    total_mtm_var.set(f"Total MTM: {tot_mtm}")
    now = datetime.now()
    time340pm = now.replace(hour=15, minute=40, second=0, microsecond=0)
    if now >= time340pm:
        update_report()

def delay_calc(secs):
    return int(secs) * 1000 

def telegram_delay_calc(mins):
    return int(float(mins)) * 60 * 1000

def refresh():
    t1 = threading.Thread(target=update, daemon=True)
    t1.start()
    DELAY = delay_calc(delay_var.get())
    root.after(DELAY, refresh)
MARKET_CLOSED = False
def telegram_update():
    global MARKET_CLOSED
    if tot_mtm == 0:
        time.sleep(2)
    if datetime.now() > time330pm:
        if not MARKET_CLOSED:
            send_telegram_message(f"MARKET CLOSED; Final MTM for {user_name} is: {tot_mtm}")
            MARKET_CLOSED = True
            return
        else:
            return
    else:
        send_telegram_message(f"The Current MTM For {user_name} is: {tot_mtm}")

def telegram_refresh():
    t1 = threading.Thread(target=telegram_update, daemon=True)
    t1.start()
    MSG_DELAY = telegram_delay_calc(telegram_delay_var.get())
    root.after(MSG_DELAY, telegram_refresh)

total_mtm_var = tk.StringVar()
total_mtm_lab = tk.Label(root, textvariable=total_mtm_var, font=font_1)
total_mtm_lab.pack(pady=10)

control_panel = tk.Frame(root)
control_panel.pack(pady=10)

delay_lab = tk.Label(control_panel, text="Delay (Secs)", font=font_2).grid(row=0, column=0, padx=5, pady=5)
delay_var = tk.StringVar(value="60")
delay = ttk.Entry(control_panel, textvariable=delay_var)
delay.grid(row=1, column=0, padx=5)

telegram_delay_lab = tk.Label(control_panel, text="Telegram Delay (Mins)", font=font_2).grid(row=0, column=1, padx=5, pady=5)
telegram_delay_var = tk.StringVar(value="15")
telegram_delay = ttk.Entry(control_panel, textvariable=telegram_delay_var)
telegram_delay.grid(row=1, column=1, padx=5)

def export_data():
    with open('data.csv', 'w', newline='') as f:
        csv_writer = csv.writer(f)
        date = datetime.now().strftime("%d-%m-%Y")
        csv_writer.writerow(("Date", "Stock", "Profit", "Loss"))
        for i in tree.get_children():
            data = tree.item(i)['values']
            if float(data[1].replace(",", "")) > 0:
                csv_writer.writerow((date, data[0], data[1], ""))
            else:
                csv_writer.writerow((date, data[0], "", data[1]))
    os.startfile('data.csv')

export_button = ttk.Button(root, text="Export", command=export_data)
export_button.pack(pady=10)

res = mb.askquestion('Telegram Updates', 'Do you want to get updates on Telegram?')
if res == 'yes':
    DEBUG = False
else:
    DEBUG = True

refresh()
telegram_refresh()
root.mainloop()
