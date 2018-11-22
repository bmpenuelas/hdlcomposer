from ghdl_tools.utils import bin_str_to



class Tick():
    """Clock shorthand

    Using one or several Tick object makes it easy to synchronize the values of
    the testbench signals.
    """

    def __init__(self, initial_tick=0):
        self.current_tick = initial_tick



    def __repr__(self):
        return 'Clock at tick ' + str(self.now)



    def tick(self, increment=1):
        self.current_tick += increment
        return self.current_tick



    @property
    def now(self):
        return self.current_tick

    @now.setter
    def now(self, value):
        self.current_tick = value



class Signal():
    """Represent a signal and encode it in Time-Value format

    The signal can be initialized with a single value or a couple of file paths like
    ['./signal_t.out', './signal_v.out'] where Time and Value can be found.

    Args:
        initial_value: Initialize the Signal.
        clock: A clock can be provided to synchronize several signals or make writing
               to this signals at different time frames more convenient.
        signal_type: Type of the signal. For example, when generating a package,
                     values will be casted to this type.
        signal_width: If signal_type has a fixed witdth, this parameter is used.
        init_files: Use a pair of time / value files to initialize the signal.
    """

    t = 0
    v = 1

    def __init__(self, initial_value, clock=None, signal_type=None, signal_width=None,
                 init_files=False):
        self.clock = clock
        self.type = signal_type
        self.width = signal_width

        self.init_files = init_files
        if init_files:
            self.waveform = []
            time = 't'
            value = 'v'
            with open(initial_value[self.t], 'r') as time_file, \
                 open(initial_value[self.v], 'r') as value_file:
                while 1:
                    try:
                        value = bin_str_to(value_file.readline()[0:-1], self.type)
                    except ValueError:
                        value = None

                    try:
                        time = int(time_file.readline()[0:-1])
                    except ValueError:
                        time = None

                    if time != None:
                        self.waveform.append([time, value])
                    else:
                        break
        else:
            self.waveform = [[0, initial_value],]

        self.next_read_tick = 0
        self.last_read_value = None



    def __repr__(self):
        return 'Signal - final value: ' + str(self.last_value)



    @property
    def len(self):
        return self.waveform[-1][self.t]



    @property
    def last_value(self):
        return self.waveform[-1][self.v]


    @property
    def val(self):
        return self.last_value


    @property
    def last_t(self):
        return self.waveform[-1][self.t]


    def get_value(self, at_tick=None, return_transition=False):
        """Get the value of the signal at a specific tick.

        Args:
            at_tick: Defaults to last value.
        """

        if (at_tick == None) or (at_tick > self.len):
            return self.last_value
        else:
            tv_i = 0
            previous = self.waveform[tv_i]
            while 1:
                if (at_tick > self.waveform[tv_i][self.t]):
                    previous = self.waveform[tv_i]
                    tv_i += 1
                else:
                    if (at_tick == self.waveform[tv_i][self.t]):
                        previous = self.waveform[tv_i]
                    break
            if return_transition:
                return previous[self.v], at_tick == previous[self.t]
            else:
                return previous[self.v]



    @property
    def current_value(self):
        return self.last_read_value



    def append(self, new_value, current_tick=None):
        """Add a new value of the signal

        If current_tick is provided, that will be used as the time value.
        Otherwise, if there is a clock attached to this signal, it will
        be used. If none of them are present, the new_value is appended one
        tick after the last time value in the waveform.
        """

        current_tick = current_tick or (self.clock.now if self.clock else None) or (self.len + 1)
        if current_tick == self.last_t:
            self.waveform[-1][self.v] = new_value
        elif new_value != self.last_value:
            self.waveform.append([current_tick, new_value])



    def read(self, ticks=1, reset=False):
        """Get the signal value at each tick

        Args:
            ticks: Number of data ticks to read.
            reset: Reset the read pointer and start reading from the first tick again.

        Returns:
            current_value: Value of the signal after reading a number of ticks.
            transitions: List of [new value, time] for each transition within the provided
                         number of ticks.
            last_tick_read: Last tick that was read.
        """

        if reset:
            self.next_read_tick = 0
            self.last_read_value = None

        transitions = []
        for i in range(ticks):
            if self.next_read_tick <= self.last_t:
                self.last_read_value, transition = self.get_value(self.next_read_tick, True)
                if transition:
                    transitions.append([self.next_read_tick, self.last_read_value])
            else:
                break
        self.next_read_tick += 1
        return self.last_read_value, transitions, (self.next_read_tick - 1)



class SignalGroup():
    """Group several signals to apply actions to all at once

    Args:
        signals (dict): {'signal_name_a': Signal(a), 'signal_name_b': Signal(b), ...}
    """

    def __init__(self, signals):
        self.signals = signals

        self.iter_index = 0



    def __repr__(self):
        return 'Signal Group - ' + ' '.join([name for name in self.signals])



    def __getattr__(self, attr):
        if attr in self.signals:
            return self.signals[attr]
        else:
            raise AttributeError('There is no attribute or signal called ' + attr)



    def __iter__(self):
        return self



    def __next__(self):
        if self.iter_index >= len(self.signal_names):
            self.iter_index = 0
            raise StopIteration
        else:
            signal = self.signals[self.signal_names[self.iter_index]]
            self.iter_index += 1
            return signal



    @property
    def signal_names(self):
        return [name for name in self.signals]



    @property
    def max_len(self):
        return max([self.signals[signal].len for signal in self.signals])



    def append(self, signals):
        if not isinstance(signals, dict):
            raise ValueError('Append signal to group requires a dict like {\'name\': Signal,}')
        for signal in signals:
            self.signals[signal] = signals[signal]



    def read(self, ticks=1, reset=False):
        values = {}
        for signal in self.signals:
            values[signal] = self.signals[signal].read(ticks, reset)
        return values



    def read_values(self, ticks=1, reset=False):
        read_result = self.read(ticks, reset)
        return {signal: read_result[signal][0] for signal in read_result}
