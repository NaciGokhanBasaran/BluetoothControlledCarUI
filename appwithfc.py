import tkinter as tk
import json
import math
import random
import serial
from datetime import datetime
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import urllib.request
import io
from config import *
import threading
import tkinter.messagebox as tk_messagebox
import face_recognition
import cv2
import numpy as np

CONFIG_PATH = "config.json"
temp_list = []
humidity_list = []
MAX_DATA_POINTS = 5

BL_connected = False
wifi_connected = False

pressed_keys = set()


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config_data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)


config = load_config()


def connect_to_wifi(stream_url):
    global wifi_connected

    try:
        urllib.request.urlopen(config["CAMERA_CONFIG"]["stream_url"]).read()
        wifi_connected = True

        camera_color = "#10b981" if wifi_connected else "#d63124"
        isWConnected_canvas.itemconfig(Wifi_status_indicator, fill=camera_color, outline=camera_color)

        update_image()
    except Exception as e:

        wifi_connected = False
        tk.messagebox.showerror("WiFi Connection Error", "Failed to connect to WiFi!")


def connect():
    global bluetooth, BL_connected

    try:
        bluetooth = serial.Serial(config['BLUETOOTH_CONFIG']['default_com_port'], 9600, timeout=1)  # bitmediii
        BL_connected = True
        # print("Bluetooth connected successfully!")
        tk.messagebox.showinfo("Success", "Bluetooth connection successful!")

        # (Optional) Update UI indicator dynamically
        canvas_color = "#10b981" if BL_connected else "#d63124"
        isConnected_canvas.itemconfig(status_indicator, fill=canvas_color, outline=canvas_color)
    except Exception as e:
        BL_connected = False
        # print(f"Bluetooth connection failed: {e}")
        tk.messagebox.showerror("Error", "Bluetooth connection failed!")


def handleKeyPress(event):
    key = event.keysym.lower()
    if key in ['w', 'a', 's', 'd', 'b'] and key not in pressed_keys:
        pressed_keys.add(key)
        send_command(key)


def handleKeyRelease(event):
    key = event.keysym.lower()
    if key in ['w', 'a', 's', 'd', 'b']:
        pressed_keys.discard(key)
        send_command('x')


def save_last5_data(row):
    if len(temp_list) >= MAX_DATA_POINTS:
        temp_list.pop(0)
        humidity_list.pop(0)

    try:
        temp_list.append(float(row['temp'].iloc[-1]))
        humidity_list.append(float(row['Humidity'].iloc[-1]))

    except (KeyError, IndexError, ValueError) as e:
        print(f"Error processing data: {e}")


def update_data():
    try:
        if bluetooth and bluetooth.in_waiting > 0:
            data = bluetooth.readline().decode('utf-8').strip()
            print(data)

            if "Temperature:" in data and ",Humidity:" in data:

                humidity_parts = data.split(",")

                if len(humidity_parts) == 2:

                    temperature = humidity_parts[0].split(":")[1].strip()
                    humidity = humidity_parts[1].split(":")[1].strip()

                    new_data = {
                        "time": [datetime.now()],
                        "temp": [temperature],
                        "Humidity": [humidity]
                    }
                    print(new_data)

                    df_new = pd.DataFrame(new_data)

                    try:

                        df_existing = pd.read_excel(sensor_data)
                    except FileNotFoundError:

                        df_existing = pd.DataFrame(columns=["time", "temp", "Humidity"])

                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    df_combined.to_excel(sensor_data, index=False)

                    save_last5_data(df_combined)
                    update_plots()
    except Exception as e:
        print(f"Error in update_data: {e}")

    root.after(1000, update_data)


def send_command(cmd):
    if bluetooth:
        try:
            bluetooth.write(cmd.encode())
            print(f"Sent: {cmd}")
        except serial.SerialException as e:

            print(f"Failed to send command: {e}")
    else:
        print("No Bluetooth connection.")


def update_plots():
    if len(temp_list) > 0 and len(humidity_list) > 0:
        temp_ax.clear()
        humidity_ax.clear()

        temp_ax.plot(temp_list, '#ff6b6b', label='Temperature')
        temp_ax.set_title('Temperature Trend')
        temp_ax.set_ylabel('°C')
        temp_ax.legend()

        humidity_ax.plot(humidity_list, '#4dd0e1', label='Humidity')
        humidity_ax.set_title('Humidity Trend')
        humidity_ax.set_ylabel('%')
        humidity_ax.legend()

        temp_canvas.draw()
        humidity_canvas.draw()


def update_image():
    def fetch_image():
        try:

            img_data = urllib.request.urlopen(config["CAMERA_CONFIG"]["stream_url"]).read()
            img = Image.open(io.BytesIO(img_data))


            frame = img.copy()
            rgb_frame = frame.convert("RGB")
            np_frame = cv2.cvtColor(np.array(rgb_frame), cv2.COLOR_RGB2BGR)


            face_locations = face_recognition.face_locations(np.array(rgb_frame))


            for top, right, bottom, left in face_locations:
                cv2.rectangle(np_frame, (left, top), (right, bottom), (0, 255, 0), 2)


            img_result = Image.fromarray(cv2.cvtColor(np_frame, cv2.COLOR_BGR2RGB))
            img_result = img_result.resize((750, 500), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(img_result)

            def update_label():
                live_video.imgtk = imgtk
                live_video.config(image=imgtk)

            root.after(0, update_label)

        except Exception as e:
            print(f"Hata: {e}")

    threading.Thread(target=fetch_image, daemon=True).start()
    root.after(100, update_image)


def update_settings():
    global bluetooth, BL_connected

    config["Data"]["file_path"] = data_entry.get()
    new_com_port = com_entry.get()
    try:
        bluetooth = serial.Serial(new_com_port, 9600, timeout=1)
        BL_connected = True
        config['BLUETOOTH_CONFIG']['default_com_port'] = new_com_port
        tk_messagebox.showinfo("Success", f"Connected to {new_com_port}")
    except:
        BL_connected = False
        tk_messagebox.showerror("Error", f"Failed to connect to {new_com_port}")

    new_stream_url = url_entry.get()
    if new_stream_url.startswith("http"):
        config["CAMERA_CONFIG"]["stream_url"] = new_stream_url
        tk_messagebox.showinfo("Success", f"Stream URL updated to {new_stream_url}")
    else:
        tk_messagebox.showerror("Error", "Invalid Stream URL")


#radar eklenmediği için sahte veri üretiyor


def draw_radar():
    radar_canvas.delete("all")

    radar_canvas.create_oval(center_x - radar_radius, center_y - radar_radius,
                             center_x + radar_radius, center_y + radar_radius,
                             outline="green", width=2)

    for angle in range(0, 181, 30):
        rad = math.radians(angle)
        x = center_x + radar_radius * math.cos(rad)
        y = center_y - radar_radius * math.sin(rad)
        radar_canvas.create_line(center_x, center_y, x, y, fill="green", dash=(2, 2), width=1)

    for angle in range(0, 181, 30):
        rad = math.radians(-angle)
        x = center_x + radar_radius * math.cos(rad)
        y = center_y - radar_radius * math.sin(rad)
        radar_canvas.create_line(center_x, center_y, x, y, fill="green", dash=(2, 2), width=1)

    for i in range(1, 4):
        radar_canvas.create_oval(center_x - i * (radar_radius // 3), center_y - i * (radar_radius // 3),
                                 center_x + i * (radar_radius // 3), center_y + i * (radar_radius // 3),
                                 outline="green", dash=(3, 5), width=1)

    angle = random.randint(0, 180)
    distance = random.randint(0, radar_radius)

    rad_angle = math.radians(angle)
    dot_x = center_x + distance * math.cos(rad_angle)
    dot_y = center_y - distance * math.sin(rad_angle)

    radar_canvas.create_oval(dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5, fill="red")  # Draw target dot

    root.after(1000, draw_radar)


if BL_connected:
    bluetooth = serial.Serial(config['BLUETOOTH_CONFIG']['default_com_port'], 9600, timeout=1)

root = tk.Tk()

root.title("Bluetooth controlled robot")
root.geometry("1500x800")
root.config(bg="#1f1f29")
root.resizable(True, True)
window_height = 800
window_width = 1500
row_size = 100
column_size = 75

# 75 x20 columns 100x8 rows
for i in range(0, int(window_height / row_size)):
    root.rowconfigure(i, minsize=row_size)
for i in range(0, int(window_width / column_size)):
    root.columnconfigure(i, minsize=column_size)

# Video Frame

video_frame = tk.Frame(root, bg="black", highlightbackground="#cccccc", highlightthickness=2)

video_frame.grid(row=0, column=0, rowspan=5, columnspan=10, sticky="nsew", padx=10, pady=10)
live_video = tk.Label(video_frame)
live_video.pack()

sensor_data = config['Data']['file_path']

# Control frame

control_frame = tk.Frame(root, bg="#2c2c3a", highlightbackground="#2c2c3a", highlightthickness=2)
control_frame.grid(row=5, column=0, rowspan=3, columnspan=4, sticky="nsew", padx=10, pady=10)

for i in range(3):
    control_frame.grid_rowconfigure(i, weight=1)
    control_frame.grid_columnconfigure(i, weight=1)

btn_w = tk.Button(control_frame, text="↑", command=lambda: send_command('w'), **btn_config)
btn_a = tk.Button(control_frame, text="←", command=lambda: send_command('a'), **btn_config)
btn_s = tk.Button(control_frame, text="↓", command=lambda: send_command('s'), **btn_config)
btn_d = tk.Button(control_frame, text="→", command=lambda: send_command('d'), **btn_config)
btn_x = tk.Button(control_frame, text="X", command=lambda: send_command('x'), **btn_x_config)

btn_w.grid(row=0, column=1, sticky="nsew", padx=7.5, pady=7.5)
btn_a.grid(row=1, column=0, sticky="nsew", padx=7.5, pady=7.5)
btn_s.grid(row=2, column=1, sticky="nsew", padx=7.5, pady=7.5)
btn_d.grid(row=1, column=2, sticky="nsew", padx=7.5, pady=7.5)
btn_x.grid(row=1, column=1, sticky="nsew", padx=7.5, pady=7.5)
#  radar  frame
# veri :açı,değer


radar_frame = tk.Frame(root, bg="#2c2c3a")
radar_frame.grid(row=5, column=4, rowspan=3, columnspan=6, sticky="nsew", padx=10, pady=10)

for i in range(3):
    radar_frame.grid_rowconfigure(i, weight=1)
    radar_frame.grid_columnconfigure(i, weight=1)

radar_canvas = tk.Canvas(radar_frame, bg="#1e1e2e", width=250, height=250, borderwidth=0, highlightthickness=0)
radar_canvas.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

radar_radius = 100
center_x = 150
center_y = 125

draw_radar()

"""humidity_label = tk.Label(root, text="Humidity: --", font=("Arial", 9))
humidity_label.place(x=650, y=25)

temperature_label = tk.Label(root, text="Temperature: --", font=("Arial", 9))
temperature_label.place(x=650, y=400)"""

fig_temp = Figure(figsize=(5, 3), dpi=80, facecolor="#2c2c3a")

temp_ax = fig_temp.add_subplot(111)

temp_ax.set_facecolor("#1e1e2e")
temp_ax.plot(temp_list, color="#ff6b6b", label='Temperature', linewidth=2)
temp_ax.set_title('Temperature Trend', color="white", fontsize=11, pad=10)
temp_ax.set_ylabel('°C', color="white", fontsize=10)
temp_ax.set_xlabel('Time', color="white", fontsize=10)
temp_ax.grid(True, linestyle='--', alpha=0.3)
temp_ax.tick_params(axis='x', colors='white')
temp_ax.tick_params(axis='y', colors='white')
for spine in temp_ax.spines.values():
    spine.set_color('white')
temp_ax.legend(facecolor="#2c2c3a", edgecolor='white', labelcolor='white')

temp_canvas = FigureCanvasTkAgg(fig_temp, master=root)

temp_canvas.get_tk_widget().grid(row=0, column=10, columnspan=4, rowspan=4, padx=10, pady=10, sticky="nsew")

fig_humidity = Figure(figsize=(5, 3), dpi=100, facecolor="#2c2c3a")
humidity_ax = fig_humidity.add_subplot(111)

humidity_ax.set_facecolor("#1e1e2e")
humidity_ax.plot(humidity_list, color="#4dd0e1", label='Humidity', linewidth=2)
humidity_ax.set_title('Humidity Trend', color="white", fontsize=11, pad=10)
humidity_ax.set_ylabel('%', color="black", fontsize=10)
humidity_ax.set_xlabel('Time', color="white", fontsize=10)
humidity_ax.grid(True, linestyle='--', alpha=0.3)
humidity_ax.tick_params(axis='x', colors='white')
humidity_ax.tick_params(axis='y', colors='white')
for spine in humidity_ax.spines.values():
    spine.set_color('white')
humidity_ax.legend(facecolor="#2c2c3a", edgecolor='white', labelcolor='white')

humidity_canvas = FigureCanvasTkAgg(fig_humidity, master=root)
humidity_canvas.get_tk_widget().grid(row=4, column=10, columnspan=4, rowspan=4, padx=10, pady=10, sticky="nsew")

# Sidebar

sidebar_frame = tk.Frame(root, bg="#2c2c3a")
sidebar_frame.grid(row=0, column=14, rowspan=8, columnspan=3, sticky="nsew", padx=10, pady=10)

for i in range(32):  # 800/32
    sidebar_frame.grid_rowconfigure(i, weight=1)
for i in range(5):  # 225/5
    sidebar_frame.grid_columnconfigure(i, weight=1)

bluetooth_button = tk.Button(sidebar_frame, text="Blueetooth", command=lambda: connect(), **bl_config)
bluetooth_button.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nsew", padx=7.5, pady=7.5)

canvas_color = "#10b981" if BL_connected else "#d63124"

isConnected_canvas = tk.Canvas(sidebar_frame, width=20, height=20, highlightthickness=0, bg="#2c2c3a")
isConnected_canvas.grid(row=0, column=3, rowspan=1, columnspan=1, padx=7.5, pady=7.5)
status_indicator = isConnected_canvas.create_oval(5, 5, 20, 20, fill=canvas_color, outline=canvas_color)

wifi_button = tk.Button(sidebar_frame, text="Wifi",
                        command=lambda: connect_to_wifi(config["CAMERA_CONFIG"]["stream_url"]), **wifi_config)
wifi_button.grid(row=1, column=0, rowspan=1, columnspan=3, sticky="nsew", padx=7.5, pady=7.5)

camera_color = "#10b981" if wifi_connected else "#d63124"

isWConnected_canvas = tk.Canvas(sidebar_frame, width=20, height=20, highlightthickness=0, bg="#2c2c3a")
isWConnected_canvas.grid(row=1, column=3, rowspan=1, columnspan=1, padx=7.5, pady=7.5)
Wifi_status_indicator = isWConnected_canvas.create_oval(5, 5, 20, 20, fill=camera_color, outline=camera_color)


com_label = tk.Label(sidebar_frame, text="COM Port:", bg="#2c2c3a", fg="white", font=("Arial", 10))
com_label.grid(row=4, column=0, columnspan=5, sticky="w", padx=7.5, pady=3)

com_entry = tk.Entry(sidebar_frame, bg="#1e1e2e", fg="white", insertbackground="white", font=("Arial", 10))
com_entry.grid(row=5, column=0, columnspan=5, sticky="nsew", padx=7.5, pady=3)
com_entry.insert(0, config['BLUETOOTH_CONFIG']['default_com_port'])  # Default value


url_label = tk.Label(sidebar_frame, text="Stream URL:", bg="#2c2c3a", fg="white", font=("Arial", 10))
url_label.grid(row=6, column=0, columnspan=5, sticky="w", padx=7.5, pady=3)

url_entry = tk.Entry(sidebar_frame, bg="#1e1e2e", fg="white", insertbackground="white", font=("Arial", 10))
url_entry.grid(row=7, column=0, columnspan=5, sticky="nsew", padx=7.5, pady=3)
url_entry.insert(0, config["CAMERA_CONFIG"]["stream_url"])



data_label = tk.Label(sidebar_frame, text="data path:", bg="#2c2c3a", fg="white", font=("Arial", 10))
data_label.grid(row=8, column=0, columnspan=5, sticky="w", padx=7.5, pady=3)

data_entry = tk.Entry(sidebar_frame, bg="#1e1e2e", fg="white", insertbackground="white", font=("Arial", 10))
data_entry.grid(row=9, column=0, columnspan=5, sticky="nsew", padx=7.5, pady=3)
data_entry.insert(0, config["Data"]["file_path"])

update_button = tk.Button(sidebar_frame, text="Update Settings", command=update_settings, bg="#10b981", fg="white",
                          font=("Arial", 10))
update_button.grid(row=11, column=0, columnspan=5, sticky="nsew", padx=7.5, pady=10)

buzzer_button = tk.Button(sidebar_frame, text="Buzz !!!", command=lambda: send_command('b'), bg="#cc0000", fg="white",
                          font=("Arial", 10))
buzzer_button.grid(row=13, column=0, rowspan=2, columnspan=5, sticky="nsew", padx=7.5, pady=10)

"""speech_button = tk.Button(sidebar_frame, text="Connect", command=lambda: connect(), **bl_config)
speech_button.grid(row=1, column=0, rowspan=1, columnspan=3, sticky="nsew", padx=7.5, pady=7.5)
#75 100"""

root.bind("<Key>", handleKeyPress)
root.bind("<KeyRelease>", handleKeyRelease)

if wifi_connected:
    update_image()

if BL_connected:
    update_data()
update_data()

root.mainloop()

new_config = {
    "BLUETOOTH_CONFIG": {
        "default_com_port": config['BLUETOOTH_CONFIG']['default_com_port']
    },
    "CAMERA_CONFIG": {
        "stream_url": config["CAMERA_CONFIG"]["stream_url"]
    },
    "Data": {
        "file_path": config["Data"]["file_path"]
    }
}

save_config(new_config)







