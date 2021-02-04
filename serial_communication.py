import argparse
from scripts.communication import IMUSerialCommunication
import time


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
            gyro_angle_x, gyro_angle_y, gyro_angle_z = serial_comm.gyroscope
            print(f"Gyroscope[deg]: {gyro_angle_x}, {gyro_angle_y}, {gyro_angle_z}")


if __name__ == "__main__":
    args = parse_args()
    main(args.port, args.baud)