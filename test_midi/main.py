from machine import Pin, Timer, UART

k_uart_id = int(0)
k_led_pin = int(25)
k_btn_pin = int(16)
k_channel = int(0)
k_program = int(0)

led = Pin(25, Pin.OUT)
timer_main = Timer()
timer_led = Timer()
uart = UART(k_uart_id)
uart.init(baudrate=31250)
btn = Pin(k_btn_pin, Pin.IN, Pin.PULL_UP)


def send(t):
    if btn.value() is not 0:
        return

    led.on()
    timer_led.init(mode=Timer.ONE_SHOT, period=100, callback=lambda t: led.off())

    uart.write(bytearray([0xC0 | k_channel, k_program]))
    uart.flush()


# The callback is delayed by 50ms. If after that period the button is not still pressed
# the action is not performed. This is to reject noise.
btn.irq(
    trigger=Pin.IRQ_FALLING,
    handler=lambda p: timer_main.init(mode=Timer.ONE_SHOT, period=50, callback=send),
)

while True:
    pass
