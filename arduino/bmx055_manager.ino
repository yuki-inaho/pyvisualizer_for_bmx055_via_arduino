#include <Wire.h>
#include <math.h>
#include <MadgwickAHRS.h>
Madgwick MadgwickFilter;

#define Addr_Accl 0x19  // (JP1,JP2,JP3 = Open)
#define Addr_Gyro 0x69  // (JP1,JP2,JP3 = Open)
#define Addr_Mag 0x13  // (JP1,JP2,JP3 = Open)

#define GYRO 1
#define ACCL 2
#define MAG 3
#define XYZ_ROTATION 4

float xAccl = 0.00;
float yAccl = 0.00;
float zAccl = 0.00;
float xGyro = 0.00;
float yGyro = 0.00;
float zGyro = 0.00;
float xMag = 0;
float yMag = 0;
float zMag = 0;
float roll = 0;
float pitch = 0;
float yaw = 0;


void write_setting(byte Addr, byte register_addr, byte setting_var, uint32_t delay_time = 100){
  Wire.beginTransmission(Addr);
  Wire.write(register_addr);  // Select register
  Wire.write(setting_var);  // Set value to register
  Wire.endTransmission();
  delay(delay_time);
}


//=====================================================================================//
void BMX055_Init() {
  //write_setting(Addr_Accl, 0x0F, 0x05); // PMU_Range register: Range = +/- 4 [g]
  write_setting(Addr_Accl, 0x0F, 0x03); // PMU_Range register: Range = +/- 2 [g]
  write_setting(Addr_Accl, 0x10, 0x08); // PMU_BW register: Bandwidth = 7.81 [Hz]
  write_setting(Addr_Accl, 0x11, 0x00); // PMU_LPW register: Normal mode, Sleep, duration = 0.5 [ms]

  write_setting(Addr_Gyro, 0x0F, 0x04); // Range register: Full scale = +/- 125 [degree/s]
  write_setting(Addr_Gyro, 0x10, 0x07); // Bandwidth register: ODR = 100 [Hz]
  write_setting(Addr_Gyro, 0x11, 0x00); // PMU_LPM1 register: Normal mode, Sleep, duration = 2.0 [ms]

  write_setting(Addr_Mag, 0x4B, 0x83); // Mag register: Soft reset
  write_setting(Addr_Mag, 0x4B, 0x01); // Mag register: Soft reset
  write_setting(Addr_Mag, 0x4C, 0x00); // Mag register: Normal mode, ODR = 10 [Hz]
  write_setting(Addr_Mag, 0x4E, 0x84); // Mag register: X, Y, Z-Axis enabled
  write_setting(Addr_Mag, 0x51, 0x04); // Mag register: Number of Repetitions for X-Y Axis = 9
  write_setting(Addr_Mag, 0x52, 0x16); // Mag register: Number of Repetitions for Z-Axis = 15
}


//=====================================================================================//
void BMX055_Accl() {
  int data[6];
  for (int i = 0; i < 6; i++) {
    Wire.beginTransmission(Addr_Accl);
    Wire.write((2 + i));  // Select data register
    Wire.endTransmission();
    Wire.requestFrom(Addr_Accl,1);  // Request 1 byte of data
    // Read 6 bytes of data
    // xAccl lsb, xAccl msb, yAccl lsb,
    // yAccl msb, zAccl lsb, zAccl msb
    if (Wire.available() == 1)
      data[i] = Wire.read();
  }

  // Convert the data to 12-bits
  xAccl = ((data[1] * 256) + (data[0] & 0xF0)) / 16;
  if (xAccl > 2047) xAccl -= 4096;
  yAccl = ((data[3] * 256) + (data[2] & 0xF0)) / 16;
  if (yAccl > 2047) yAccl -= 4096;
  zAccl = ((data[5] * 256) + (data[4] & 0xF0)) / 16;
  if (zAccl > 2047) zAccl -= 4096;

  // renge +-2g
  xAccl = xAccl * 0.0098;
  yAccl = yAccl * 0.0098;
  zAccl = zAccl * 0.0098;
}


void BMX055_Gyro() {
  int data[6];
  for (int i = 0; i < 6; i++) {
    Wire.beginTransmission(Addr_Gyro);
    Wire.write((2 + i));  // Select data register
    Wire.endTransmission();
    Wire.requestFrom(Addr_Gyro, 1);  // Request 1 byte of data
    // Read 6 bytes of data
    // xGyro lsb, xGyro msb, yGyro lsb,
    // yGyro msb, zGyro lsb, zGyro msb
    if (Wire.available() == 1)
      data[i] = Wire.read();
  }
  // Convert the data
  xGyro = (data[1] * 256) + data[0];
  if (xGyro > 32767) xGyro -= 65536;
  yGyro = (data[3] * 256) + data[2];
  if (yGyro > 32767) yGyro -= 65536;
  zGyro = (data[5] * 256) + data[4];
  if (zGyro > 32767) zGyro -= 65536;

  // Full scale = +/- 125 [degree/s]
  xGyro = xGyro * 0.0038;
  yGyro = yGyro * 0.0038;
  zGyro = zGyro * 0.0038;
}


void BMX055_Mag() {
  int data[8];
  for (int i = 0; i < 8; i++) {
    Wire.beginTransmission(Addr_Mag);
    Wire.write((0x42 + i));  // Select data register
    Wire.endTransmission();
    Wire.requestFrom(Addr_Mag, 1);  // Request 1 byte of data
    // Read 6 bytes of data
    // xMag lsb, xMag msb, yMag lsb,
    // yMag msb, zMag lsb, zMag msb
    if (Wire.available() == 1)
      data[i] = Wire.read();
  }
  // Convert the data
  xMag = ((data[1] << 8) | (data[0] >> 3));
  if (xMag > 4095) xMag -= 8192;
  yMag = ((data[3] << 8) | (data[2] >> 3));
  if (yMag > 4095) yMag -= 8192;
  zMag = ((data[5] << 8) | (data[4] >> 3));
  if (zMag > 16383) zMag -= 32768;
}


//=====================================================================================//
void quaternion_filtering(){
  //MadgwickFilter.update(xGyro, yGyro, zGyro, xAccl, yAccl, zAccl, xMag, yMag, zMag);
  MadgwickFilter.updateIMU(xGyro, yGyro, zGyro, xAccl, yAccl, zAccl);
  roll = MadgwickFilter.getRoll();
  pitch = MadgwickFilter.getPitch();
  yaw = MadgwickFilter.getYaw();
}

void setup() {
  Wire.begin();  // Wire (Arduino-I2C)
  Serial.begin(115200);
  BMX055_Init();
  delay(300);
  // Sampling Frequency = 30 [Hz]; https://courses.cs.washington.edu/courses/cse466/14au/labs/l4/madgwick_internal_report.pdf
  MadgwickFilter.begin(30);
}

void print_sensor_value_triplet(String sensor_type, float x_value, float y_value, float z_value){
  Serial.print(sensor_type);
  Serial.print(",");
  Serial.print(x_value);
  Serial.print(",");
  Serial.print(y_value);
  Serial.print(",");
  Serial.println(z_value);
}

void loop() {
  BMX055_Gyro();
  //print_sensor_value_triplet("GYRO:", xGyro, yGyro, zGyro);

  BMX055_Accl();
  //print_sensor_value_triplet("ACCL:", xAccl, yAccl, zAccl);

  BMX055_Mag();
  //print_sensor_value_triplet("MAG:", xMag, yMag, zMag);

  quaternion_filtering();
  print_sensor_value_triplet("RPY Degrees", roll, pitch, yaw);
}