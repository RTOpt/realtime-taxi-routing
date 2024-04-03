from datetime import datetime, timedelta

class Timer:
    def __init__(self):
        """
        Initializes the Timer object with default values.
        """
        self._cpu_since_start = timedelta(0)
        self._cpu_since_init = timedelta(0)
        self._cpu_init = datetime.now()
        self._is_started = False
        self._is_stopped = False

    def start(self):
        """
        Starts the timer.
        """
        self.start_time = datetime.now()
        self.is_started = True
        self.is_stopped = False

    def stop(self):
        """
        Stops the timer and calculates the elapsed time since the timer was started.
        """
        if not self.is_started:
            raise Exception("Timer not started.")
        end_time = datetime.now()
        self.cpu_since_start = end_time - self.start_time
        self.cpu_since_init += self.cpu_since_start
        self.is_stopped = True
        self.is_started = False

    def d_since_init(self):
        """
        Returns the total elapsed time since the timer was initialized.
        """
        return self.cpu_since_init.total_seconds()

    def d_since_start(self):
        """
        Returns the elapsed time since the timer was started.
        """
        if not self.is_started and not self.is_stopped:
            raise Exception("Timer not started or stopped.")
        return self.cpu_since_start.total_seconds()

    # Getters and setters

    @property
    def cpu_since_start(self):
        return self._cpu_since_start

    @cpu_since_start.setter
    def cpu_since_start(self, value):
        self._cpu_since_start = value

    @property
    def cpu_since_init(self):
        return self._cpu_since_init

    @cpu_since_init.setter
    def cpu_since_init(self, value):
        self._cpu_since_init = value

    @property
    def cpu_init(self):
        return self._cpu_init

    @cpu_init.setter
    def cpu_init(self, value):
        self._cpu_init = value

    @property
    def is_started(self):
        return self._is_started

    @is_started.setter
    def is_started(self, value):
        self._is_started = value

    @property
    def is_stopped(self):
        return self._is_stopped

    @is_stopped.setter
    def is_stopped(self, value):
        self._is_stopped = value
