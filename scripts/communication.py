import serial
import struct
from typing import NamedTuple, List
from datetime import datetime
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
        dt_now = datetime.now()
        print(f"[{dt_now}] The connection between GXM550 is established")
        self._ser.open()

    def close(self):
        dt_now = datetime.now()
        print(f"[{dt_now}] The connection between GXM550 is closed")
        self._ser.close()

    def update(self) -> bool:
        status = self._ser.inWaiting() != 0
        if status:
            status = self._get_imu_info()
        return status

    def _parse_imu_info(self, splitted_packet_list: List[str]) -> None:
        new_information = {}
        field_names = self._imu_info._fields
        for k, name in zip(range(1, SIZEOF_IMU_PACKET, 4), field_names):  # Remove overhead & delimiter bytes
            byte_list = splitted_packet_list[k : k + 4]
            if len(byte_list) < 4:
                continue

            # FIXME: byte must be in range(0, 256)
            try:
                decoded_value = struct.unpack("<f", bytearray([int(word, 16) for word in byte_list]))[0]
            except struct.error as err:
                print(err)
            new_information[name] = decoded_value

        self._imu_info = IMUInformation(
            xAccl=new_information["xAccl"],
            yAccl=new_information["yAccl"],
            zAccl=new_information["zAccl"],
            xGyro=new_information["xGyro"],
            yGyro=new_information["yGyro"],
            zGyro=new_information["zGyro"],
            is_valid=True
        )

    def _get_imu_info(self) -> bool:
        packet = self._ser.readline()
        splitted_packet_list = packet.split(b' ')[:-1]  # Remove newline character
        is_recieved_data_valid = len(splitted_packet_list) == SIZEOF_IMU_PACKET
        if is_recieved_data_valid:
            self._parse_imu_info(splitted_packet_list)
        return is_recieved_data_valid

    @property
    def data_status(self) -> bool:
        return self._imu_info.is_valid

    @property
    def data(self) -> IMUInformation:
        return self._imu_info

    @property
    def gyroscope(self) -> List[float]:
        return [self._imu_info.xGyro, self._imu_info.yGyro, self._imu_info.zGyro] # by [Degrees]

    @property
    def accelerometer(self) -> List[float]:
        return [self._imu_info.xAccl, self._imu_info.yAccl, self._imu_info.zAccl]
