import sys
import argparse
from scripts.communication import IMUSerialCommunication
from datetime import datetime
from collections import deque

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import time


def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--port", "-p", type=str, default="/dev/ttyACM0", help="name of serial port for communication")
    parser.add_argument("--baud", "-b", type=int, default=115200, help="Baud-rate for serial communication")
    return parser.parse_args()


# 描画用の関数
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
    return figure_canvas_agg


def animate(i):
    x_values.append(next(index))
    y_values.append(random.randint(0, 5))
    plt.cla()
    plt.plot(x_values, y_values)


def main(port_name: str, baudrate: int):
    serial_comm = IMUSerialCommunication(port_name, baudrate)
    serial_comm.open()

    layout = [
        [sg.Canvas(key="-CANVAS-")],
    ]
    window = sg.Window("Gyroscope Demo", layout, finalize=True, element_justification="center", font="Monospace 18")

    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(111)
    ax.set_ylim(-60, 60)

    gyro_x_deque = deque(maxlen=90)
    gyro_y_deque = deque(maxlen=90)
    gyro_z_deque = deque(maxlen=90)
    time_deque = deque(maxlen=90)

    # Set Dummy data
    for i in range(10):
        gyro_x_deque.append(0)
        gyro_y_deque.append(0)
        gyro_z_deque.append(0)
        time_deque.append(0)

    canvas = window["-CANVAS-"].TKCanvas
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel("Angle [deg]")
    ax.set_ylabel("Elapsed time [s]")
    plt.legend()
    ax.grid()
    fig_agg = draw_figure(canvas, fig)

    start_time_seconds = round(time.time() * 10e6)
    while True:
        event, values = window.read(timeout=10)

        dt_now = datetime.now()
        current_time_seconds = round(time.time() * 10e6)
        diff_seconds = current_time_seconds - start_time_seconds

        if event in ("Exit", None):
            sys.exit(0)

        if serial_comm.update():
            gyro_angle_x, gyro_angle_y, gyro_angle_z = serial_comm.gyroscope
            print(f"[{dt_now}] Gyroscope : {gyro_angle_x:4.5} [deg], {gyro_angle_y:4.5} [deg], {gyro_angle_z:4.5} [deg]")

            gyro_x_deque.append(gyro_angle_x)
            gyro_y_deque.append(gyro_angle_y)
            gyro_z_deque.append(gyro_angle_z)
            time_deque.append(diff_seconds)
        else:
            print(f"[{dt_now}] IMU Update Failed...")

        ax.cla()
        ax.grid()
        ax.plot(time_deque, gyro_x_deque, label="x", color="red")
        ax.plot(time_deque, gyro_y_deque, label="y", color="green")
        ax.plot(time_deque, gyro_z_deque, label="z", color="blue")
        fig_agg.draw()

    window.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.port, args.baud)