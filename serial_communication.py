import argparse
from scripts.communication import IMUSerialCommunication
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--port", "-p", type=str, default="/dev/ttyACM0", help="name of serial port for communication")
    parser.add_argument("--baud", "-b", type=int, default=115200, help="Baud-rate for serial communication")
    return parser.parse_args()


def main(port_name: str, baudrate: int):
    serial_comm = IMUSerialCommunication(port_name, baudrate)
    serial_comm.open()
    while True:
        if serial_comm.update():
            dt_now = datetime.now()
            gyro_angle_x, gyro_angle_y, gyro_angle_z = serial_comm.gyroscope
            print(f"[{dt_now}] Gyroscope : {gyro_angle_x:3.5} [deg], {gyro_angle_y:3.5} [deg], {gyro_angle_z:3.5} [deg]")


if __name__ == "__main__":
    args = parse_args()
    main(args.port, args.baud)