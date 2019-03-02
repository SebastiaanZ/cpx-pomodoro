from time import monotonic, sleep

import lib.adafruit_circuitplayground.cexpress as cexpress


class Express(cexpress.Express):
    '''
    Subclass of the standard Express class. Since the class is
    already instantiated in the original express.mpy file, I've
    created and cross-compiled an identical express file, without
    the instantiating of cpx.
    '''
    def __init__(self):
        super().__init__()
        self.last_button_a = monotonic()
        self.last_button_b = monotonic()

        self.sensitivity = 0.25

    @property
    def single_press_a(self):
        '''
        Detects a single click of button a. A single click is
        defined as a press shorter than self.sensitivity. This
        suppresses accidental double detections.
        '''
        if not self.button_a:
            return False

        if (monotonic() - self.last_button_a) > self.sensitivity:
            self.last_button_a = monotonic()
            return True

        return False

    @property
    def single_press_b(self):
        '''
        Detects a single click of button b. A single click is
        defined as a press shorter than self.sensitivity. This
        suppresses accidental double detections.
        '''
        if not self.button_b:
            return False

        if (monotonic() - self.last_button_b) > self.sensitivity:
            self.last_button_b = monotonic()
            return True

        return False


class Pomodoro:
    def __init__(self, usb_down=True):
        # Default interval times in minutes; can be changed using attributes
        self.work_duration = 45
        self.short_break = 10
        self.long_break = 20
        self.schedule = ["w", "sb", "w", "lb", "w", "sb", "w"]

        # Interval attributes and LED color
        self.intervals = {
            "w": ("_work_duration", (0, 0, 5)),
            "sb": ("_short_break", (0, 5, 0)),
            "lb": ("_long_break", (4, 1, 3)),
        }

        # Settings related to idle led
        self.idle_update = 0.5
        self.idle_led = 0
        self.idle_time = monotonic()

        # Decide start_led based on orientation
        self.start_led = 4 if usb_down else 9
        self.stop_led = 5 if usb_down else 0

    @property
    def work_duration(self):
        return self._work_duration / 60

    @work_duration.setter
    def work_duration(self, duration):
        if duration <= 0:
            raise ValueError("The duration must larger than zero")
        self._work_duration = duration * 60

    @property
    def short_break(self):
        return self._short_break / 60

    @short_break.setter
    def short_break(self, duration):
        if duration <= 0:
            raise ValueError("The duration must larger than zero")
        self._short_break = duration * 60

    @property
    def long_break(self):
        return self._long_break / 60

    @long_break.setter
    def long_break(self, duration):
        if duration <= 0:
            raise ValueError("The duration must larger than zero")
        self._long_break = duration * 60

    def idle_animation(self):
        '''Idle animation of one light going round the board'''
        if (monotonic() - self.idle_time) > self.idle_update:
            cpx.pixels[self.idle_led] = (0, 0, 0)
            self.idle_led = (self.idle_led - 1) % 10
            cpx.pixels[self.idle_led] = (0, 5, 0)
            self.idle_time = monotonic()

    def blink(self):
        '''Blinks LEDs by toggling current state with off-state'''
        if cpx.pixels[:] == self.led_state:
            cpx.pixels[:] = [(0, 0, 0)] * 10
        else:
            cpx.pixels[:] = self.led_state

    def pause(self):
        '''Blinking lights when an interval is paused'''
        pause_time = monotonic()
        self.led_state = cpx.pixels[:]
        while True:
            if (monotonic() - pause_time) > 0.3:
                self.blink()
                pause_time = monotonic()
            if cpx.single_press_a or cpx.single_press_b:
                cpx.pixels[:] = self.led_state
                return

    def interval(self, duration, color=(0, 0, 5)):
        '''Represents one interval within a worksession'''
        cpx.pixels[:] = [color] * 10
        led_start = monotonic()
        led_duration = duration / 10
        led_current = self.start_led

        while True:
            if (monotonic() - led_start) > led_duration:
                cpx.pixels[led_current] = (0, 0, 0)
                if led_current == self.stop_led:
                    if cpx.switch:
                        cpx.play_tone(1720, 0.1)
                    return
                led_current = (led_current - 1) % 10
                led_start = monotonic()

            if cpx.single_press_a:
                pre_pause = monotonic()
                self.pause()
                led_start += monotonic() - pre_pause

            if cpx.single_press_b:
                for _ in range(2):
                    cpx.pixels[:] = [(10, 0, 0)] * 10
                    sleep(0.2)
                    cpx.pixels[:] = [(0, 0, 0)] * 10
                    sleep(0.1)
                return

    def work_session(self):
        '''Controls the work session using the schedule'''
        for period in self.schedule:
            duration, color = self.intervals[period]
            duration = getattr(self, duration)
            self.interval(duration, color)

    def start(self):
        while True:
            self.idle_animation()
            if cpx.single_press_a:
                self.work_session()


# New cpx instance from the subclassed Express class
cpx = Express()
