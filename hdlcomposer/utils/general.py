from os         import (listdir, walk, getcwd)
from os.path    import (normpath, abspath, join, isdir)
from subprocess import (check_output, Popen, DEVNULL, STDOUT, check_call,
                        CalledProcessError)



###############################################################################
# GENERIC HELPER FUNCTIONS
###############################################################################

def save_txt(text, path):
    """Save text string as file
    """

    with open(path, "w+") as f:
        f.write(''.join(text.split('\n')))



def get_bit(y, x):
    """Get single bit at index
    """

    return str((x>>y)&1)



def int_tobin(x, count=8):
    """ Integer to binary string
    """

    shift = range(count - 1, -1, -1)
    bits = map(lambda y: get_bit(y, x), shift)
    return "".join(bits)



def bin_str_to(bin_str, signal_type):
    """Binary string to boolean or integer

    Conversion depends on the signal type.
    """

    if bin_str == None:
        return None

    if signal_type in ('boolean', 'std_logic',):
        return (False if (bin_str.lower() in ('0', 'false')) else True)
    elif signal_type in ('integer', 'unsigned', 'std_logic_vector'):
        return int(bin_str, 2)
    elif signal_type == 'signed':
        if bin_str[0] == '0':
            return bin_str_to(bin_str[1:], 'integer')
        else:
            return -1 * (~((bin_str_to(bin_str[1:], 'integer') - 1)) & (2**(len(bin_str) - 1) - 1))
    else:
        raise ValueError('Conversion to ' +  signal_type + 'is not available. Supported types: \
                          boolean, std_logic, std_logic_vector, integer, signed, unsigned')



def vd_files(signal_name, directory_path):
    """Return a pair of typical file paths for a VHDL signal dump
    """

    return [join(directory_path, signal_name + '_t.out'), join(directory_path, signal_name + '_v.out')]



def data_to_pkg_cfg(data):
    """Generate the config structure needed to generate a VHDL package from Signal(s) or Constant(s)

    Args:
        data: A dictionary like {'signal_name_a': Signal(a), 'constant_a': Constant(b), ...} or
              a Group instance.
    """

    from hdlcomposer.signals import (Group, Signal, Constant)
    if isinstance(data, Group):
        elements = data.elements
    else:
        if not all([type(obj) in (Signal, Constant) for obj in data.values()]):
            raise TypeError('Provide a Group or dictionary containing Signal and/or Constant objects')
        else:
            elements = data

    pkg_cfg = {}
    for element_name in elements.keys():
        if isinstance(elements[element_name], Signal):
            pkg_cfg[element_name.upper() + '_T'] = {
                'data': [data[Signal.t] for data in elements[element_name].waveform],
                'type': 'integer',
            }
            pkg_cfg[element_name.upper() + '_V'] = {
                'data': [data[Signal.v] for data in elements[element_name].waveform],
                'type': elements[element_name].type,
                'width': elements[element_name].width,
            }
        elif isinstance(elements[element_name], Constant):
            pkg_cfg[element_name.upper()] = {
                'data': elements[element_name].value,
                'type': elements[element_name].type,
                'width': elements[element_name].width,
            }
    return pkg_cfg



def run_console_command(command):
    """Run a command in the console

    Returns:
        error
        terminal_output
    """

    try:
        terminal_output = check_output(command, shell=True)
        error = 0
    except CalledProcessError as err:
        terminal_output = err.output
        error = err.returncode
    try:
        terminal_output = terminal_output.decode('utf-8')
    except Exception as e:
        terminal_output = 'Error decoding terminal output.'
    return error, terminal_output



def get_dirs_inside(dir_path):
    """Get a list of all the subdirectories inside a given directory
    """

    scan_folder = normpath(dir_path)
    return [abspath(join(scan_folder, d)) for d in listdir(scan_folder)
            if isdir(join(scan_folder, d))]



def get_filepaths_recursive(dir_path, extensions=[], include_files=[], exclude_files=[]):
    """Get a list of all the files inside a given directory

    This function is recursive, it will scan all directories inside
    every subdirectory recursively.
    """

    scan_folder = normpath(dir_path)
    file_paths = []

    for root, dirs, files in walk(scan_folder):
        for file in files:
            if (not(include_files) or (file in include_files)) and (file not in exclude_files):
                if extensions:
                    for extension in [ext.lower() for ext in extensions]:
                        if file.lower().endswith(extension):
                            file_path = join(root, file)
                            file_paths.append(file_path)
                else:
                    file_path = join(root, file)
                    file_paths.append(file_path)
    return file_paths



def get_dirs_containing_files(dir_path, extension=None):
    """Get a list of all the directories that contain a file with the given extension

    Extension is optional (to find non-empty directories). This function is recursive,
    it will scan all directories inside every subdirectory recursively.
    """

    scan_folder = normpath(dir_path)
    found_dirs = []
    for root, dirs, files in walk(scan_folder):
        for file in files:
            if (not extension) or file.lower().endswith(extension.lower()):
                found_dirs.append(root)
    return found_dirs



def gtkwave_open_wave(ghw_path, gtkw_file=''):
    """Open a ghw file in GTKWave

    Optionally, you can provide a gtkw file too.
    """

    command_open_wave = 'gtkwave "' + ghw_path + '"'
    if gtkw_file:
        command_open_wave += ' -a "' + gtkw_file + '"'
    Popen(command_open_wave, stdout=DEVNULL, stderr=STDOUT)
