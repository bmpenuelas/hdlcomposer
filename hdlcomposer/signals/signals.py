from hdlcomposer.utils.general import (bin_str_to)



class Tick():
    """Clock shorthand

    Using one or several Tick objects makes synchronizing the values of the testbench
    signals easy.
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



class Constant():
    """Constant value
    """

    def __init__(self, value, constant_type=None, constant_width=None):
        self.value = value
        self.type = constant_type
        self.width = constant_width



    def __repr__(self):
        return 'Constant - value: ' + str(self.value)



class Signal():
    """Represent a signal and encode it in Time-Value format

    The signal can be initialized with a single value or a couple of file paths like
    ['./signal_t.out', './signal_v.out'] where Time and Value can be found.

    Args:
        initial_value: Initialize the Signal.
        signal_type: Type of the signal. For example, when generating a package,
                     values will be casted to this type.
        signal_width: If signal_type has a fixed witdth, this parameter is used.
        clock_write, clock_read: Clocks to assign or read the signal at different
                                 ticks.
        period (str time): Optionally define a time magnitude for each tick.
        init_files: Use a pair of time / value files to initialize the signal.
    """

    t = 0
    v = 1

    def __init__(self, initial_value=None, signal_type=None, signal_width=None, clock_write=None,
                 clock_read=None, period=None, init_files=False, signal_path=''):
        self.type = signal_type
        self.width = signal_width
        self.clock_write = clock_write or Tick()
        self.clock_read = clock_read or Tick()
        self.last_read_value = None
        self.period = period
        self.signal_path = signal_path

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
        elif initial_value != None:
            self.waveform = [[0, initial_value],]



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

        If current_tick is provided, the write clock tick will be moved forward up to
        current_tick.
        """

        if current_tick:
            self.clock_write.now = current_tick
        if self.clock_write.now == self.last_t:
            self.waveform[-1][self.v] = new_value
        elif new_value != self.last_value:
            self.waveform.append([self.clock_write.now, new_value])



    def read(self, ticks=1, reset=False):
        """Get the signal value at each tick

        Args:
            ticks: Number of data ticks to read.
            reset: Reset the read pointer and start reading from the first tick again.

        Returns:
            current_value: Value of the signal after reading a number of ticks.
            transitions: List of [new value, tick] for each transition within the provided
                         number of ticks.
            last_tick_read: Last tick that was read.
        """

        if reset:
            self.clock_read.now = 0
            self.last_read_value = None

        transitions = []
        for i in range(ticks):
            if self.clock_read.now <= self.last_t:
                self.last_read_value, transition = self.get_value(self.clock_read.now, True)
                if transition:
                    transitions.append([self.clock_read.now, self.last_read_value])
            else:
                break
        self.clock_read.tick()
        return self.last_read_value, transitions, (self.clock_read.now - 1)



class Group():
    """Group several signals and or constants to apply actions to all at once

    Args:
        elements (dict): {'signal_name_a': Signal(a), 'constant_a': Constant(a), ...}
    """

    def __init__(self, elements):
        self.signals = {}
        self.constants = {}
        self.elements = elements

        self.iter_index = 0



    @property
    def elements(self):
        return {**self.constants, **self.signals}



    @elements.setter
    def elements(self, new):
        for name in new:
            if isinstance(new[name], Signal):
                self.signals[name] = new[name]
            elif isinstance(new[name], Constant):
                self.constants[name] = new[name]
            else:
                raise TypeError('Provide a dictionary containing Signal and/or Constant objects')



    @property
    def element_names(self):
        return [name for name in self.elements]



    @property
    def max_len(self):
        return max([self.signals[signal].len for signal in self.signals])



    def __repr__(self):
        return 'Group - ' + ' '.join([name for name in self.elements])



    def __getattr__(self, attr):
        if attr in self.elements:
            return self.elements[attr]
        else:
            raise AttributeError('There is no attribute or element called ' + str(attr))



    def __iter__(self):
        return self



    def __next__(self):
        if self.iter_index >= len(self.element_names):
            self.iter_index = 0
            raise StopIteration
        else:
            element = self.elements[self.element_names[self.iter_index]]
            self.iter_index += 1
            return element



    def append(self, elements):
        if not isinstance(elements, dict):
            raise ValueError('Append to group requires a dict like {\'name\': new_element,}')
        for element in elements:
            self.elements[element] = elements[element]



    def read(self, ticks=1, reset=False):
        values = {}
        for signal in self.signals:
            values[signal] = self.signals[signal].read(ticks, reset)
        return values



    def read_values(self, ticks=1, reset=False):
        read_result = self.read(ticks, reset)
        return {signal: read_result[signal][0] for signal in read_result}
