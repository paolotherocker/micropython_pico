from machine import Pin, Timer, PWM, UART

k_uart_id = 0
k_led_pin = 25
k_channel = 0
k_program = 0

led = Pin(25, Pin.OUT)
timer_main = Timer()
timer_led = Timer()
uart = UART(k_uart_id)
uart.init(baudrate=31250)


def send(timer: Timer):
    led.on()
    timer_led.init(mode=Timer.ONE_SHOT, period=100, callback=lambda t: led.off())

    uart.write(bytearray([0xC0 | k_channel, k_program]))
    uart.flush()


timer_main.init(mode=Timer.PERIODIC, period=1000, callback=send)

while True:
    pass
