import serial
from cobs import cobs
from typing import NamedTuple, List
import struct

import pdb


SIZEOF_IMU_PACKET = 26  # size([xAccl, yAccl, zAccl, xGyro, yGyro, zGyro]) * sizeof(float) + "overhead byte" + "delimiter byte" = 6*4 + 1 + 1 = 26

# TODO: add timestamp information
IMUInformation = NamedTuple(
    "IMUInformation", [("xAccl", float), ("yAccl", float), ("zAccl", float), ("xGyro", float), ("yGyro", float), ("zGyro", float), ("is_valid", bool)]
)


class IMUSerialCommunication:
    def __init__(self, port_name: str, baudrate: int, timeout: float = 1.0):
        self._ser = serial.Serial(timeout=timeout)
        self._ser.port = port_name
        self._ser.baudrate = baudrate
        self._ser.setDTR(False)  # Prevend to reset

        # Set dummy data
        self._imu_info: IMUInformation = IMUInformation(xAccl=0, yAccl=0, zAccl=0, xGyro=0, yGyro=0, zGyro=0, is_valid=False)

    def __del__(self):
        self._ser.close()

    def open(self):
        self._ser.open()

    def close(self):
        self._ser.close()

    def update(self) -> bool:
        status = self._ser.inWaiting() != 0
        if status:
            status = self._get_imu_info()
        return status

    def _parse_imu_info(self, splitted_packet_list: List[str]) -> None:
        field_names = self._imu_info._fields
        for k, name in zip(range(1, SIZEOF_IMU_PACKET, 4), field_names):  # Remove overhead & delimiter bytes
            byte_list = splitted_packet_list[k : k + 4]
            decoded_value = struct.unpack("<f", bytearray([int(word, 16) for word in byte_list]))[0]
            setattr(self._imu_info, name, decoded_value)
        setattr(self._imu_info, "is_valid", True)

    def _get_imu_info(self) -> bool:
        packet = str(self._ser.readline(), "utf-8")
        splitted_packet_list = packet.split(" ")[:-1]  # Remove newline character
        is_recieved_data_valid = len(splitted_packet_list) == SIZEOF_IMU_PACKET
        if is_recieved_data_valid:
            self._parse_imu_info(splitted_packet_list)
        return is_recieved_data_valid

    @property
    def imu_informations(self) -> IMUInformation:
        return self._imu_info