# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 01:42:52 2020

@author: parkbumjin
"""

import serial

ser = serial.Serial(

    port='COM3', # 컴포트는 장치관리자에서 꼭 확인하세요.

    baudrate=115200,

    parity=serial.PARITY_NONE,

    stopbits=serial.STOPBITS_ONE,

    bytesize=serial.EIGHTBITS,

        timeout=0)

print(ser.portstr) #연결된 포트 확인.

ser.write(bytes('hello', encoding='ascii')) #출력방식1

ser.write(b'hello') #출력방식2

ser.write(b'\xff\xfe\xaa') #출력방식3

#출력방식4

vals = [12, 0, 0, 0, 0, 0, 0, 0, 7, 0, 36, 100] 

ser.write(bytearray(vals))

ser.read(ser.inWaiting()) #입력방식1

ser.close()