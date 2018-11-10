
###############################################################################
# Object-Oriented VHDL Units representation
###############################################################################

# Constants

TAB = 2
GENERATE_STATEMENTS = ['if-generate', 'for-generate']



# Classes

class Tick():

    def __init__(self, initial_value=0):
        self.current_value = initial_value



    def __repr__(self):
        return 'Clock at tick ' + str(self.now)



    def tick(self, increment=1):
        self.current_value += increment



    @property
    def now(self):
        return self.current_value

    @now.setter
    def now(self, value):
        self.current_value = value



class Signal():
    """Represent a signal and encode it in Value-Duration format

    The signal can be initialized with a single value or a couple of file paths like
    ['signal_v.out', 'signal_d.out'] where Value and Duration can be found.
    """

    def __init__(self, initial_value, clock=None, signal_type=None, signal_width=None,
                 init_files=False):
        self.clock = clock
        self.type = signal_type
        self.width = signal_width

        if init_files:
            self.waveform = []
            value = 'v'
            duration = 'd'
            with open(initial_value[0], 'r') as value_file, \
                 open(initial_value[1], 'r') as duration_file:
                while duration:
                    try:
                        value = int(value_file.readline()[0:-1], 2)
                    except ValueError:
                        value = None

                    try:
                        duration = int(duration_file.readline()[0:-1])
                    except ValueError:
                        duration = None

                    self.waveform.append([value, duration])
        else:
            self.waveform = [[initial_value, None],]

        self.next_read_tick = 0
        self.read_block = 0
        self.read_block_tick = 0
        self.last_read_value = None



    def __repr__(self):
        return 'Signal - final value: ' + str(self.last_value)



    @property
    def len(self):
        return sum([block[1] for block in self.waveform if block[1]])



    @property
    def last_value(self):
        return self.waveform[-1][0]



    def get_value(self, at_tick=None):
        """Get the value of the signal at a specific tick.

        Args:
            at_tick: Defaults to last value.
        """

        if not at_tick or at_tick > self.len:
            return self.last_value
        else:
            current_block = 0
            accum = at_tick
            while 1:
                if accum > (self.waveform[current_block][1] - 1):
                    accum -= self.waveform[current_block][1]
                    current_block += 1
                else:
                    return self.waveform[current_block][0]



    @property
    def current_value(self):
        return str(self.last_read_value)



    def append(self, new_value, current_tick=None):
        """Add a new value of the signal
        """

        if not (current_tick or self.clock):
            current_tick = self.len + 1
        if new_value != self.waveform[-1][0]:
            self.waveform[-1][1] = (current_tick or self.clock.now) - self.len
            self.waveform.append([new_value, None])



    def end(self, current_tick=None):
        """Complete the waveform
        """

        if not (current_tick or self.clock):
            current_tick = self.len + 1
        if self.waveform[-1][1] == None:
            self.waveform[-1][1] = (current_tick or self.clock.now) + 1 - self.len



    def read(self, ticks=1, reset=False):
        """Get the signal value at each tick

        Args:
            ticks: Number of data ticks to read.

        Returns:
            current_value: Value of the signal after reading a number of ticks.
            transitions: List of [new_value, time] for each transition within the provided
                         number of ticks.
            last_tick_read: Last tick that was read.
        """

        if reset:
            self.next_read_tick = 0
            self.read_block = 0
            self.read_block_tick = 0
            self.last_read_value = None

        if len(self.waveform) > self.read_block:
            transitions = []
            for i in range(ticks):
                if self.next_read_tick == 0:
                    self.last_read_value = self.waveform[0][0]
                if self.read_block_tick >= self.waveform[self.read_block][1]:
                    self.read_block += 1
                    self.read_block_tick = 0
                    self.last_read_value = self.waveform[self.read_block][0]
                    transitions.append([self.last_read_value, self.next_read_tick])
                self.next_read_tick += 1
                self.read_block_tick += 1
            return self.current_value, transitions, (self.next_read_tick - 1)
        else:
            return None, [], (self.next_read_tick - 1)



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
            raise ValueError('Append signal to group requires a dict like {\'name\': Signal}')
        for signal in signals:
            self.signals[signal] = signals[signal]



    def end(self, params=None):
        for signal in self.signals:
            if isinstance(params, dict):
                end_tick = params[signal] if (params and (signal in params)) else None
            else:
                end_tick = params
            self.signals[signal].end(end_tick)



    def read(self, ticks=1):
        values = {}
        for signal in self.signals:
            values[signal] = self.signals[signal].read(ticks)
        return values



class Unit():
    """Base unit with common properties
    """

    def __init__(self, name, parent, indentation):
        self.name = name
        self.parent = parent
        self.indentation = indentation



    def print_children(self):
        self.print_hierarchy(self)



    @staticmethod
    def print_hierarchy(element):
        print(' ' * element.indentation + str(element))
        if element.children:
            for child in element.children:
                element.print_hierarchy(child)



class Generate(Unit):
    """If-generate or for-generate statements
    """

    def __init__(self, name, parent, indentation, value, generates=None, instances=None):
        super().__init__(name, parent, indentation)
        self.value = value
        self.generates = generates or []
        self.instances = instances or []
        setattr(parent, name, self)
        parent.generates.append(self)


    def __repr__(self):
        return self.type + ' ' + self.name

    def __str__(self):
        return self.name


    @property
    def type(self):
        return self.__class__.__name__


    @property
    def children(self):
        return self.generates + self.instances



class Entity(Unit):
    """VHDL Entity
    """

    def __init__(self, name, parent, indentation, arch='', generates=None, instances=None,
                 ports=None, signals=None, processes=None):
        super().__init__(name, parent, indentation)
        self.arch = arch
        self.generates = generates or []
        self.instances = instances or []
        self.ports = ports or []
        self.signals = signals or []
        self.processes = processes or []
        setattr(parent, name, self)
        parent.entity = self


    def __repr__(self):
        return self.type + ' ' + self.name

    def __str__(self):
        return self.name


    @property
    def type(self):
        return self.__class__.__name__


    @property
    def children(self):
        return self.generates + self.instances



class Instance(Unit):
    """Instance of a VHDL entity
    """

    def __init__(self, name, indentation, parent=None, entity=None):
        super().__init__(name, parent, indentation)
        self.entity = entity or {}
        if parent:
            setattr(parent, name, self)
            parent.instances.append(self)


    def __repr__(self):
        return self.type + ' ' + self.name

    def __str__(self):
        return self.name


    @property
    def type(self):
        return self.__class__.__name__


    @property
    def children(self):
        return [self.entity]



class Top(Instance):
    """Top entity
    """

    def __init__(self, name, packages=None):
        super().__init__(name, parent=None, indentation=-TAB)
        self.packages = packages or []
