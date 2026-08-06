"""
Install dependencies:
mpremote mip install usb-device-midi tm1637
"""

import time
import machine
import sys

led = machine.Pin("LED", machine.Pin.OUT)


def blink(n):
    for _ in range(n):
        led.on()
        time.sleep_ms(100)
        led.off()
        time.sleep_ms(100)


blink(1)  # Reached start of script

try:
    import usb.device
    from usb.device.midi import MIDIInterface

    midi = MIDIInterface()
    blink(2)  # MIDIInterface object created

    usb.device.get().init(
        midi, builtin_driver=True, product_str="MicroPython CC Button"
    )
    blink(3)  # init() returned, USB re-enumeration triggered

    while not midi.is_open():
        time.sleep_ms(100)
    blink(4)  # Host has opened the MIDI interface, ready to send

except Exception as e:
    with open("error_log.txt", "w") as f:
        sys.print_exception(e, f)
    while True:
        blink(6)  # Crashed, check error_log.txt

while True:
    led.on()
    midi.control_change(0, 64, 127)
    time.sleep_ms(1000)
    midi.control_change(0, 64, 0)
    led.off()
    time.sleep_ms(1000)
