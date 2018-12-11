from re import compile, sub, escape



###############################################################################
# REGULAR EXPRESSIONS
###############################################################################

# Parse GHDL output

re_find_name_and_unit = compile('(?P<name>[\w|\(|\)|\.]+)\s\[(?P<unit>(if-generate|for-generate|instance|arch|entity|package)).*\]')

def get_name_and_unit(line):
    find_name_and_unit_result = re_find_name_and_unit.search(line)
    if find_name_and_unit_result:
        name = find_name_and_unit_result.group('name')
        name = sub(r'\((?P<index>\d+)\)', '\\1', name)
        unit = find_name_and_unit_result.group('unit')
    else:
        name, unit = ('', '')
    return name, unit



re_find_value = compile('(?P<value>(true|false))\]')

re_find_indentation = compile('(?P<indentation>\W*)\w')

re_index = compile('\((?P<index>\d+)\)')

re_include_output = compile('(?P<type>(entity|package))\s(?P<name>\w+)')

re_vend_srcs = compile('SourceDirectories\[(?P<name>\w+)\]\s*=\s*"(?P<path>(\w|\/|\.)+)')



# Parse VCD

def find_signal_name(line, name='', path='', is_array=False):
    if (not name in line) or (not path in line):
        return False, None

    find_name_expression = \
        r'^.*?(\.|\\|\/)?' + \
        r'(?P<name>[\w|\[|\]]+)' + \
        (r'\[(?P<array_high>(\d)+)\:(?P<array_low>(\d))+\]$' \
         if is_array else r'$')
    re_find_signal_name = compile(find_name_expression)

    found_signal_name = None
    path_matches = False
    if re_find_signal_name.match(line):
        found_signal_name = re_find_signal_name.search(line).group('name')
        found_array_high = re_find_signal_name.search(line).group('array_high') if is_array else ''
        found_array_low = re_find_signal_name.search(line).group('array_low') if is_array else ''

        if (found_signal_name == name) or (name == line):
            match_path_expression = \
                r'^.*?(\.|\\|\/)?' + \
                escape(path) + \
                escape(found_signal_name) + \
                (r'\[(?P<array_high>' + found_array_high + r')\:(?P<array_low>' + found_array_low + r')+\]$' \
                 if is_array else r'$')
            re_match_path = compile(match_path_expression)
            path_matches = True if re_match_path.match(line) else False
    return path_matches, found_signal_name
