"""A MicroPython class that extends the built-in `neopixel.NeoPixel` driver
with a *subset-based* API:

- add_subset(length=None)  -> pre-register a contiguous block of `length`
                               pixels (taken from wherever the previous
                               subset left off). Returns an auto-incrementing
                               integer id (0, 1, 2, ...) used to address that
                               block later. If `length` is None, the subset
                               swallows every pixel not yet claimed by an
                               earlier subset.
- fill(color, id=None)     -> fill a previously-registered subset (by id)
                               with a solid colour. If `id` is None, fills
                               whatever pixels are still unclaimed by any
                               subset ("the rest of the strip").
- add_pulse(id=None, ...)  -> register a sine-wave pulse on a subset (by id),
                               or on the unclaimed remainder if `id` is None.
                               Re-calling with the same id replaces that
                               subset's pulse.
- remove_pulse(id)         -> stop the pulse (if any) attached to a subset id
                               (or to the "remainder" if id is None).
- clear_pulses()           -> remove all registered pulses (pixels left
                               as-is).
- clear()                  -> stop all pulses AND blank every pixel, but
                               keep the subset structure (ids stay valid).
- reset()                  -> like clear(), but also forgets the subset
                               structure -- add_subset() must be called again
                               from scratch afterwards.
- update()                 -> recomputes the current colour of every active
                               pulse based on elapsed time (does NOT call
                               write()).
- poll()                   -> convenience helper: calls update() then
                               write().

Type hints use only builtin types (int, float, str, bool, tuple, dict, list)
so no extra imports (e.g. `typing`) are required -- important on MicroPython
where the `typing` module is usually unavailable and generic subscripting
such as `tuple[int, int]` is not supported on the class objects themselves.
Where a value may legitimately be `None` (e.g. an un-set default), that is
called out in the docstring rather than via `Optional[...]`.

Typical usage on a board with NeoPixels on GPIO 4:

from machine import Pin
from neopixelmanager import NeoPixelManager
import time

np = NeoPixelManager(Pin(4), 30)  # 30 pixel strip
np.reset()

# Pre-declare two subsets: first 8 pixels, next 16 pixels.
id_a = np.add_subset(8)      # id_a == 0, covers pixels 0-7
id_b = np.add_subset(16)     # id_b == 1, covers pixels 8-23

# Static fill on subset 0
np.fill((0, 0, 255), id=id_a)

# Pulse subset 1 between two colours
np.add_pulse(id=id_b, color1=(255, 0, 0), color2=(0, 0, 0), period_ms=2000)

# Anything left over (pixels 24-29) can be addressed with id=None
np.fill((0, 255, 0), id=None)

np.write()

while True:
    np.poll()  # updates pulsing pixels and pushes to the strip
    time.sleep_ms(20)

np.clear()   # stop pulses + blank strip, subsets 0 and 1 still valid
np.reset()   # stop pulses + blank strip + forget subsets entirely
"""

import time
import math
import neopixel
from machine import Pin


class NeoPixelManager(neopixel.NeoPixel):
    """NeoPixel strip with pre-declared subsets, fill-by-id, and pulsing."""

    def __init__(self, pin_id: int, n: int, bpp: int = 3, timing: int = 1) -> None:
        """
        Args:
            pin_id (int): machine pin ID
            n (int): number of LEDs in the array
            bpp (int, optional): is 3 for RGB LEDs, and 4 for RGBW LEDs.
            timing (int, optional): is 0 for 400KHz, and 1 for 800kHz LEDs
                (most are 800kHz)
        """
        super().__init__(Pin(pin_id), n, bpp, timing)
        self._subsets: dict = {}  # id -> (start, length)
        self._next_subset_id: int = 0
        self._cursor: int = 0  # first pixel not yet claimed by a subset
        self._pulses: dict = {}  # id (or None) -> pulse state dict

    # ------------------------------------------------------------------
    # Subset management
    # ------------------------------------------------------------------
    def add_subset(self, length: int = None) -> int:
        """Pre-register a contiguous block of pixels for later addressing.

        The block starts wherever the previous subset (if any) left off.

        Args:
            length (int, optional): number of pixels to claim; None claims
                every pixel not yet owned by an earlier subset.

        Returns:
            int: auto-generated numeric id (0, 1, 2, ...) for this subset,
                used with fill()/add_pulse()/remove_pulse().
        """
        n: int = len(self)
        start: int = self._cursor
        if length is None:
            length = max(0, n - start)

        subset_id: int = self._next_subset_id
        self._next_subset_id += 1
        self._subsets[subset_id] = (start, length)
        self._cursor = min(n, start + length)
        return subset_id

    def _resolve_range(self, subset_id: int) -> tuple:
        """Translate a subset id (or None) into a (start, length) tuple.

        `subset_id=None` maps to whatever pixels remain unclaimed by any
        subset (from the current cursor to the end of the strip).
        """
        if subset_id is None:
            n: int = len(self)
            start: int = self._cursor
            length: int = max(0, n - start)
            return start, length

        return self._subsets[subset_id]

    # ------------------------------------------------------------------
    # Basic pixel operations
    # ------------------------------------------------------------------
    def fill(self, color: tuple, id: int = None) -> None:
        """Fill a subset (or the unclaimed remainder) with a solid colour.

        Args:
            color (tuple): tuple matching the strip's bpp, e.g. (r, g, b)
            id (int, optional): id returned from add_subset(); None targets
                whatever pixels are not yet claimed by any subset.
        """
        n: int = len(self)
        start, length = self._resolve_range(id)

        first: int = max(0, start)
        last: int = min(n, start + length)

        for i in range(first, last):
            self[i] = color

    def clear(self) -> None:
        """
        Stop all active pulses and blank every pixel, keeping the
        underlying subset structure intact (ids remain valid).

        Call write() afterwards to push the change to the physical strip.
        """
        self.clear_pulses()
        off: tuple = (0, 0, 0) if self.bpp == 3 else (0, 0, 0, 0)
        n: int = len(self)
        for i in range(n):
            self[i] = off

    def reset(self) -> None:
        """
        Stop all active pulses, blank every pixel, and forget the subset
        structure entirely. add_subset() must be called again afterwards
        to re-establish ids.

        Call write() afterwards to push the change to the physical strip.
        """
        self.clear()
        self._subsets = {}
        self._next_subset_id = 0
        self._cursor = 0

    # ------------------------------------------------------------------
    # Pulsing support
    # ------------------------------------------------------------------
    def add_pulse(
        self,
        color1: tuple,
        color2: tuple,
        period_ms: int,
        id: int = None,
        phase_deg: float = 0,
    ) -> int:
        """Register (or replace) a sine-wave pulse on a subset.

        Args:
            color1 (tuple): colour at the trough of the sine wave (t = 0)
            color2 (tuple): colour at the peak of the sine wave (t = 1)
            period_ms (int): full pulse period in milliseconds (one
                complete color1 -> color2 -> color1 cycle)
            id (int, optional): id returned from add_subset(); None targets
                whatever pixels are not yet claimed by any subset.
            phase_deg (float, optional): optional phase offset in degrees,
                so multiple pulses can be started out of sync

        Returns:
            int: the id this pulse is attached to (echoes `id`, or the
                sentinel used for "unclaimed remainder" pulses).

        Note:
            Calling add_pulse() again with the same `id` replaces any
            existing pulse on that subset.
        """
        start, length = self._resolve_range(id)

        self._pulses[id] = {
            "start": start,
            "length": length,
            "color1": tuple(color1),
            "color2": tuple(color2),
            "period_ms": period_ms,
            "phase": math.radians(phase_deg),
            "t0": time.ticks_ms(),
        }
        return id

    def remove_pulse(self, id: int = None) -> bool:
        """Stop and forget the pulse attached to a subset id.

        Args:
            id (int, optional): id returned from add_subset() (or None for
                the "unclaimed remainder" pulse).

        Returns:
            bool: True if a matching pulse was found and removed,
                False otherwise
        """
        if id in self._pulses:
            del self._pulses[id]
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

        for pulse in self._pulses.values():
            period: int = pulse["period_ms"]
            elapsed: int = time.ticks_diff(now, pulse["t0"])

            theta: float = (2 * math.pi * elapsed / period) + pulse["phase"]
            t: float = (math.sin(theta) + 1) / 2  # normalised to [0, 1]

            color: tuple = self._interp(pulse["color1"], pulse["color2"], t)

            n: int = len(self)
            first: int = max(0, pulse["start"])
            last: int = min(n, pulse["start"] + pulse["length"])
            for i in range(first, last):
                self[i] = color

    def poll(self) -> None:
        """Convenience helper: update() all pulses then push to the strip."""
        self.update()
        self.write()
