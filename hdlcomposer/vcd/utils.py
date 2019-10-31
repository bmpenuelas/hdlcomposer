from vcdvcd                import (VCDVCD)

from hdlcomposer.vcd.parse import (find_signal_name)



def get_signal_names(vcd_path):
    """Load a vcd file and return the list of signal names including path
    """

    vcd = VCDVCD(vcd_path)
    return vcd.get_signals()



def get_data(vcd_path):
    """Load a vcd file and return the list of signal names including path
    """

    vcd = VCDVCD(vcd_path)
    return vcd.get_data()



def vcd_to_signals(vcd_path, signals='', module_path=''):
    """Load a vcd file times and values into Signals

    Args:
        vcd_path: Path to the .vcd file.
        signals: Name(s) of the signals to load. None or [] loads them all.
        module_path: Path of the signal(s) in the RTL hierarchy. A string to
                     apply to all the signals, or a dictionary {name: path,}
                     if a list of signals is provided.
                     In order to select signals by module (and differentiate
                     signals with equal names located in different modules),
                     provide the path to the signals that you want to extract.
                     Example:
                     Signals in the vcd file:
                       'dut.Top/uAdder/data[15:0]',
                       'dut.Top/uAdder/en',
                       'dut.Top/uAdder/dv',
                       'dut.Top/uMux/data[31:0]',
                       'dut.Top/uMux/en',
                       'dut.Top/uMux/dv',
                     Setting signals_base_path='uMux/' will return:
                       {'data': Signal(this will be 'dut.Top/uMux/data[31:0]'),
                        'en':   Signal(this will be 'dut.Top/uMux/en'),
                        'dv':   Signal(this will be 'dut.Top/uMux/dv')}
    """

    from hdlcomposer.signals import Signal

    vcd = VCDVCD(vcd_path)
    signals_in_vcd = vcd.get_signals()
    data = vcd.get_data()

    result_signals = {}

    if not signals:
        signals = signals_in_vcd
    elif not isinstance(signals, list):
        signals = [signals]
    if not isinstance(module_path, dict):
        module_path = {name: module_path for name in signals}

    for identifier in data:
        signal_names_in_id = data[identifier]['references']
        for vcd_signal_name in signal_names_in_id:
            for signal_name in module_path:
                size = int(data[identifier]['size'])
                matches, found_signal_name = find_signal_name(
                    vcd_signal_name,
                    signal_name,
                    module_path[signal_name],
                    (size > 1)
                )
                if matches:
                    module_path.pop(signal_name)
                    result_signals[found_signal_name] = Signal(signal_type=data[identifier]['var_type'],
                                                               signal_width=int(data[identifier]['size']),
                                                               signal_path=vcd_signal_name)
                    result_signals[found_signal_name].waveform = [list(tv) for tv in data[identifier]['tv']]
                    break

    return result_signals
