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
        serial_comm.update()


if __name__ == "__main__":
    args = parse_args()
    main(args.port, args.baud)