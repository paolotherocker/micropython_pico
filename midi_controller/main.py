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
import time
from patch_manager import PatchManager

# SSD1306
p_disp_sda = 2
p_disp_scl = 3
# Neopixel pins
p_np = 15
k_np_strip_len = 8  # Number of leds per strip
k_np_strip_num = 4  # Number of strips
# Control pins
p_controls = [10, 11, 12, 13]
# Encoder pins
p_rotary_clk = 16
p_rotary_dt = 17
p_rotary_sw = 18
# Extra button pins
p_menu_buttons = [19, 20]

controls = [Button(p, debounce_ms=100) for p in p_controls]
encoder = Rotary(dt_pin=p_rotary_dt, clk_pin=p_rotary_clk)

np_array = NeoPixelManager(pin_id=p_np, n=k_np_strip_len * k_np_strip_num)
for i in range(k_np_strip_num):
    np_array.add_subset(k_np_strip_len)

patch_manager = PatchManager(controls=controls, np=np_array, encoder=encoder)
patch_manager.c_active_1 = [(0, 200, 32), (0, 32, 200)]
patch_manager.c_active_2 = [(0, 200, 96), (0, 96, 200)]
patch_manager.c_passive = [(0, 100, 48), (0, 48, 100)]
patch_manager.preset_up = 2
patch_manager.preset_down = 3
patch_manager.preset_num = 16

while True:
    patch_manager.update()
    time.sleep_ms(5)
