"""
Install dependencies:
mpremote mip install usb-device-midi neopixel ssd1306
mpremote fs cp -r lib_common :/lib
"""

from machine import Pin
from micropython import const
from lib_common.button import Button, ButtonEvent
from lib_common.rotary import Rotary, RotaryEvent
from lib_common.neopixelmanager import NeoPixelManager

# SSD1306 I2C pins
p_disp_sda = 2
p_disp_scl = 3
# Neopixel pins
p_np = [6, 7, 8, 9]
# Number of leds per strip
k_np_num = 8
# Control pins
p_controls = [10, 11, 12, 13]
# Encoder pins
p_rotary_clk = 16
p_rotary_dt = 17
p_rotary_sw = 18
# Extra button pins
p_menu_buttons = [19, 20]
