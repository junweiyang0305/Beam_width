import serial
import time
import csv
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 115200
PRONTO_PORT  = "COM5"
PRONTO_BAUD  = 115200
N_CYCLES     = 8000
STEPS_PER_CYCLE = 3
CSV_FILE     = "beam_profile.csv"

# Functions
def read_pronto_power(port=PRONTO_PORT,
                      baudrate=PRONTO_BAUD,
                      timeout=0.5) -> float:
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            time.sleep(0.1)
            ser.write(b"*CVU\r\n")
            raw = ser.readline().decode('ascii').strip()
            return float(raw) if raw else 0.0
    except:
        return 0.0

def single_step_and_read_position(ser: serial.Serial,
                                  steps: int = 1) -> int:
    ser.reset_input_buffer()
    cmd = f"{steps}\n".encode('ascii')
    ser.write(cmd)
    while True:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line.lstrip('-').isdigit():
            return int(line)

# 流程
# 準備CSV
with open(CSV_FILE, "w", newline="") as f:
    csv.writer(f).writerow(["Step", "Power_uW", "Timestamp"])

# 打開arduino接口
arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=0.5)
time.sleep(2)
arduino.reset_input_buffer()

try:
    for cycle in range(1, N_CYCLES+1):
        # 走10步
        pos = single_step_and_read_position(arduino, steps=STEPS_PER_CYCLE)

        # 讀powermeter, 换算成 µW
        p_w = read_pronto_power()
        p_uw = p_w * 1e6

        # 記錄到CSV
        ts = datetime.now().isoformat(sep=' ', timespec='seconds')
        with open(CSV_FILE, "a", newline="") as f:
            csv.writer(f).writerow([pos, f"{p_uw:.2f}", ts])

        # 輸出進度
        print(f"[{ts}] Cycle {cycle}/{N_CYCLES}: "
              f"Step={pos}, Power={p_uw:.2f} µW")

        time.sleep(0.1)

finally:
    arduino.close()

# 分析
df = pd.read_csv(CSV_FILE)
x = df["Step"].values
y = df["Power_uW"].astype(float).values
y_norm = y / y.max()

idx90 = next((i for i,v in enumerate(y_norm) if v <= 0.90), None)
idx10 = next((i for i,v in enumerate(y_norm) if v <= 0.10), None)
if idx90 is None or idx10 is None:
    raise RuntimeError("无法定位 90% 或 10% 点")

d_index = idx10 - idx90
beam_width = d_index * 0.78 * STEPS_PER_CYCLE * 1.673e-6  # m

print(f"\n→ x90 idx={idx90}, x10 idx={idx10}, Δidx={d_index}")
print(f"光束寬度: {beam_width:.6e} m")

# 作圖
plt.figure(figsize=(6,4))
plt.plot(x, y_norm*100, '-', label="Normalized Power (%)")
plt.scatter([x[idx90]], [y_norm[idx90]*100], c='red', label='90%')
plt.scatter([x[idx10]], [y_norm[idx10]*100], c='red', label='10%')
plt.xlabel("Step")
plt.ylabel("Power (%)")
plt.title("Knife-Edge Profile")
plt.grid(True)
plt.legend()
plt.show()
