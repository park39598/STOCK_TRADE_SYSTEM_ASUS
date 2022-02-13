# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 23:16:24 2020

@author: parkbumjin
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
 
x= np.arange(0,640,1)             # points in the x axis
y= np.arange(0,480,1)             # points in the y axis
X, Y= np.meshgrid(x, y)               # create the "base grid"
Z= X**2 - Y**2                               # points in the z axis
 
fig= plt.figure()
ax= fig.gca(projection='3d')             # 3d axes instance
surf= ax.plot_surface(X, Y, Z,          # data values (2D Arryas)
                       rstride=2,                   # row step size
                       cstride=2,                  # column step size
                       cmap=cm.RdPu,       # colour map
                       linewidth=1,               # wireframe line width
                       antialiased=True)
 
ax.set_title('Hyperbolic Paraboloid')       # title
ax.set_xlabel('x label')                            # x label
ax.set_ylabel('y label')                            # y label
ax.set_zlabel('z label')                            # z label
fig.colorbar(surf, shrink=0.5, aspect=5)  # colour bar
 
ax.view_init(elev=30,azim=70)               # elevation & angle
ax.dist=8                                                  # distance from the plot
plt.show()

import cv2

import numpy as np

import ctypes

from ctypes import *
from PIL import Image
path_dll = 'D:\\DEBUG\\DDE_DLL\\Digital_Detailed_Enhancement\\{out}\\x64\\Release\\Digital_Detailed_Enhancement.dll'
DDE = cdll.LoadLibrary(path_dll)
path='E:\\SNAP1.png'
img = cv2.imread(path)
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def GET_DDE_IMG(img):
    dwCount = c_long(int(img.shape[0]) * int(img.shape[1]))
    m_pImage = create_string_buffer(b'\000' * dwCount.value)
    c_short_p = ctypes.POINTER(ctypes.c_long)
    
    img_p = img.ctypes.data_as(c_short_p)
    DDE.RunDDE.argtypes = [c_short_p, c_void_p, c_int, c_int, c_byte]
    DDE.RunDDE.restype = None
    test = DDE.RunDDE(img_p, m_pImage, c_int(img.shape[1]), c_int(img.shape[0]), c_byte(8))
    DDE_img = Image.frombytes('L', (img.shape[1], img.shape[0]), m_pImage)
    del m_pImage
    return DDE_img
