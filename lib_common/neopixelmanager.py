"""
neopixelmanager.py

A MicroPython class that extends the built-in `neopixel.NeoPixel` driver with:

- fill(color, start, length) -> overridden to fill only a subset of pixels
- reset()                    -> blacks out the whole strip AND stops all
                                 active pulses
- add_pulse(...)             -> register a subset of pixels to pulse
                                 between two colours with a given period
                                 (ms), using a sine-wave envelope for a
                                 smooth breathing effect. Returns an
                                 auto-generated numeric pulse id.
- remove_pulse(pulse_id)     -> stop a pulse by the id returned from
                                 add_pulse()
- clear_pulses()             -> remove all registered pulses (pixels left
                                 as-is)
- update()                   -> recomputes the current colour of every
                                 active pulse based on elapsed time (does
                                 NOT call write())
- poll()                     -> convenience helper: calls update() then
                                 write()

Type hints use only builtin types (int, float, str, bool, tuple, dict, list)
so no extra imports (e.g. `typing`) are required -- important on MicroPython
where the `typing` module is usually unavailable and generic subscripting
such as `tuple[int, int]` is not supported on the class objects themselves.
Where a value may legitimately be `None` (e.g. an un-set default), that is
called out in the docstring rather than via `Optional[...]`.

Typical usage on a board with NeoPixels on GPIO 4:

    from machine import Pin
    from pulsing_neopixel import NeoPixelManager
    import time

    np = NeoPixelManager(Pin(4), 30)  # 30 pixel strip
    np.reset()

    # Pulse pixels 0-9 between red and off, once every 2 seconds
    pulse_id = np.add_pulse(start=0, length=10,
                             color1=(255, 0, 0), color2=(0, 0, 0),
                             period_ms=2000)

    # Static fill for pixels 10-19
    np.fill((0, 0, 255), start=10, length=10)
    np.write()

    while True:
        np.poll()  # updates pulsing pixels and pushes to the strip
        time.sleep_ms(20)

    np.reset()  # later, stop all pulses and blank the strip
"""

import time
import math
import neopixel


class NeoPixelManager(neopixel.NeoPixel):
    """NeoPixel strip with subset-fill, reset, and sine-wave pulsing."""

    def __init__(self, pin, n: int, bpp: int = 3, timing: int = 1) -> None:
        super().__init__(pin, n, bpp, timing)
        self._pulses: list = []
        self._next_pulse_id: int = 0

    # ------------------------------------------------------------------
    # Basic pixel operations
    # ------------------------------------------------------------------
    def fill(self, color: tuple, start: int = 0, length: int = None) -> None:
        """
        Fill a contiguous subset of the strip with a single colour.

        :param color: tuple matching the strip's bpp, e.g. (r, g, b)
        :param start: index of the first pixel to fill (default 0)
        :param length: number of pixels to fill; None defaults to
            "rest of strip"
        """
        n: int = len(self)
        if length is None:
            length = n - start

        first: int = max(0, start)
        last: int = min(n, start + length)

        for i in range(first, last):
            self[i] = color

    def reset(self) -> None:
        """
        Stop all active pulses and blank every pixel on the strip.

        Call write() afterwards to push the change to the physical strip.
        """
        self.clear_pulses()
        off: tuple = (0, 0, 0) if self.bpp == 3 else (0, 0, 0, 0)
        self.fill(off, 0, len(self))

    # ------------------------------------------------------------------
    # Pulsing support
    # ------------------------------------------------------------------
    def add_pulse(
        self,
        start: int,
        length: int,
        color1: tuple,
        color2: tuple,
        period_ms: int,
        phase_deg: float = 0,
    ) -> int:
        """
        Register a new sine-wave pulse on a subset of pixels.

        :param start: first pixel index in the subset
        :param length: number of pixels in the subset
        :param color1: colour at the trough of the sine wave (t = 0)
        :param color2: colour at the peak of the sine wave (t = 1)
        :param period_ms: full pulse period in milliseconds (one complete
            color1 -> color2 -> color1 cycle)
        :param phase_deg: optional phase offset in degrees, so multiple
            pulses can be started out of sync
        :return: auto-generated numeric id for this pulse, used
            to remove it later via remove_pulse()
        """
        pulse_id: int = self._next_pulse_id
        self._next_pulse_id += 1

        self._pulses.append(
            {
                "pulse_id": pulse_id,
                "start": start,
                "length": length,
                "color1": tuple(color1),
                "color2": tuple(color2),
                "period_ms": period_ms,
                "phase": math.radians(phase_deg),
                "t0": time.ticks_ms(),
            }
        )

        return pulse_id

    def remove_pulse(self, pulse_id: int) -> bool:
        """
        Stop and forget a pulse by its id.

        :param pulse_id: id returned from add_pulse()
        :return: True if a matching pulse was found and removed,
            False otherwise
        """
        for i, pulse in enumerate(self._pulses):
            if pulse["pulse_id"] == pulse_id:
                del self._pulses[i]
                return True
        return False

    def clear_pulses(self) -> None:
        """Remove all registered pulses (pixels are left as-is)."""
        self._pulses.clear()

    @staticmethod
    def _interp(color1: tuple, color2: tuple, t: float) -> tuple:
        """Linearly interpolate between two colours at fraction t in [0, 1]."""
        return tuple(
            int(color1[i] + (color2[i] - color1[i]) * t) for i in range(len(color1))
        )

    def update(self) -> None:
        """
        Recompute the colour of every active pulse's subset based on the
        current time and write those values into the pixel buffer.

        The blend fraction follows a sine wave: t = (sin(theta) + 1) / 2,
        which eases smoothly in and out of each colour (a "breathing"
        effect) rather than moving linearly like a triangle wave.

        This does NOT push data to the physical strip -- call write()
        (or the poll() helper below) afterwards to do that.
        """
        now: int = time.ticks_ms()

        for pulse in self._pulses:
            period: int = pulse["period_ms"]
            elapsed: int = time.ticks_diff(now, pulse["t0"])

            theta: float = (2 * math.pi * elapsed / period) + pulse["phase"]
            t: float = (math.sin(theta) + 1) / 2  # normalised to [0, 1]

            color: tuple = self._interp(pulse["color1"], pulse["color2"], t)
            self.fill(color, pulse["start"], pulse["length"])

    def poll(self) -> None:
        """Convenience helper: update() all pulses then push to the strip."""
        self.update()
        self.write()
