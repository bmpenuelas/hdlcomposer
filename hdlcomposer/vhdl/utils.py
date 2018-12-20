from os.path           import (join)

from hdlcomposer.utils import (int_tobin, data_to_pkg_cfg)



def generate_vhdl_package(pkg_cfg, package_name, output_directory=None, indentation=2):
    """Generate a VHDL package with the provided constants

    Data can be provided as integer, as a binary representation string, or even as
    a mix of the two.
    Width will be extended according to the type.

    Supported types: boolean, std_logic, std_logic_vector, integer, signed, unsigned
                     (and arrays of those types)

    Args:
        pkg_cfg (dict): A dictionary containing all the signals to be
            included in the package with the following format:

            pkg_cfg = {
                'constant_0': {
                    'data': [1, '0'],
                    'type': 'boolean'
                },
                'constant_1': {
                    'data': [1, '0'],
                    'type': 'std_logic'
                },
                'constant_2': {
                    'data': 8,
                    'type': 'integer',
                    'width': None,
                },
                'constant_3': {
                    'data': [244, 1, -1, '11100', '0101'],
                    'type': 'signed',
                    'width': 9,
                },
                'constant_4': {
                    'data': ['1001', 1, 32],
                    'type': 'unsigned',
                    'width': 17,
                },
                'constant_5': {
                    'data': [24, 8932, '10101110110110', 142],
                    'type': 'std_logic_vector',
                    'width': 14,
                },
            }

        package_name (str): Package name.
        output_directory (str): Output path.

    Returns:
        bool: The return value. True for error, False otherwise.
    """

    file_path = join((output_directory or getcwd()), package_name + '.vhd')

    package_text = []
    package_text.append('')

    package_text.append('library   ieee;')
    package_text.append('use       ieee.std_logic_1164.all;')
    package_text.append('use       ieee.numeric_std.all;')
    package_text.append('')

    package_text.append('package ' + package_name + ' is')
    package_text.append('')


    for constant_name in pkg_cfg.keys():
        data_w = pkg_cfg[constant_name]['width'] if ('width' in pkg_cfg[constant_name].keys()) else None
        data_type = pkg_cfg[constant_name]['type']

        package_text.append(' ' * 1 * indentation)

        if isinstance(pkg_cfg[constant_name]['data'], list):
            is_array = True
        else:
            is_array = False
            pkg_cfg[constant_name]['data'] = [pkg_cfg[constant_name]['data']]
        array_len = len(pkg_cfg[constant_name]['data'])


        if is_array:
            package_text[-1] += 'type T_' + constant_name.upper() + ' is array(0 to '
            package_text[-1] += str(array_len) + ' - 1) of '

            if data_type in ('boolean', 'std_logic', 'integer'):
                package_text[-1] += data_type + ';'
            else:
                package_text[-1] += data_type + '(' + str(data_w)
                package_text[-1] += ' - 1 downto 0);'

            package_text.append(' ' * 1 * indentation)


        package_text[-1] += 'constant ' + constant_name.upper() + ' : '
        if is_array:
            package_text[-1] += 'T_' + constant_name.upper()
        else:
            if data_type in ('boolean', 'std_logic', 'integer'):
                package_text[-1] += data_type
            else:
                package_text[-1] += data_type + '(' + str(data_w)
                package_text[-1] += ' - 1 downto 0)'
        package_text[-1] += ' := '


        if is_array:
            package_text[-1] += '('
            if array_len == 1:
                package_text[-1] += ' 0 => '


        for i in range(array_len):
            data_i = pkg_cfg[constant_name]['data'][i]

            if is_array:
                package_text.append(' ' * 2 * indentation)

            if data_type in 'boolean':
                boolean_value = 'true' if (data_i and (isinstance(data_i, str) \
                                       and data_i.lower() not in ('false', '0'))) \
                                       else 'false'
                package_text[-1] += boolean_value
            elif data_type in 'std_logic':
                package_text[-1] += '\'1\'' if data_i else '\'0\''
            elif data_type in 'integer':
                package_text[-1] += str(data_i)
            elif data_type in ('signed', 'unsigned', 'std_logic_vector'):
                package_text[-1] += '"'
                if isinstance(data_i, str):
                    if len(data_i) > data_w:
                        raise ValueError('Data width is larger that the provided width parameter.')
                    fill_char = (data_i[0] if data_type == 'signed' else '0')
                    package_text[-1] += (data_w - len(data_i)) * fill_char + data_i
                if isinstance(data_i, int):
                    package_text[-1] += int_tobin(data_i, data_w)
                else:
                    raise ValueError('Data type must be binary representation string or int.')
                package_text[-1] += '"'
            else:
                raise ValueError('Type ' +  data_type + ' is not supported yet.')

            if not i == array_len - 1:
                package_text[-1] += ','

        if is_array:
            package_text.append('')
            package_text[-1] += ' ' * 1 * indentation + ')'
        package_text[-1] += ';'
        package_text.append('')


    package_text.append('end ' + package_name + ';')


    with open(file_path, 'w') as f:
        for line in package_text:
            f.write(line + '\n')



def data_to_package(signals, package_name, output_dir=None):
        """Generate a VHDL package from a group of signals
        """

        generate_vhdl_package(data_to_pkg_cfg(signals), package_name, output_dir)
