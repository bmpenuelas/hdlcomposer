from re                      import (compile, sub)
from hdl_composer.vhdl.units import *



re_find_name_and_unit = compile('(?P<name>[\w|\(|\)|\.]+)\s\[(?P<unit>(if-generate|for-generate|instance|arch|entity|package)).*\]')

re_find_value = compile('(?P<value>(true|false))\]')

re_find_indentation = compile('(?P<indentation>\W*)\w')

re_index = compile('\((?P<index>\d+)\)')

re_include_output = compile('(?P<type>(entity|package))\s(?P<name>\w+)')



def get_name_and_unit(line):
    find_name_and_unit_result = re_find_name_and_unit.search(line)
    if find_name_and_unit_result:
        name = find_name_and_unit_result.group('name')
        name = sub(r'\((?P<index>\d+)\)', '\\1', name)
        unit = find_name_and_unit_result.group('unit')
    else:
        name, unit = ('', '')
    return name, unit



def get_indentation(line):
    indentation_result = re_find_indentation.search(line)
    return len( indentation_result.group('indentation') )



def get_parent(unit, indentation):
    if indentation == 0:
        return None

    found = False
    check_unit = unit
    while check_unit.indentation != indentation:
        check_unit = check_unit.parent
        found = True

    if not found:
        raise ValueError('Parent not found.')
    return check_unit.parent



def get_generate_value(line):
    find_value_result = re_find_value.search(line)
    return (False if find_value_result and find_value_result.group('value')=='false' else True)



def parse_included(include_terminal_output):
    result = []
    for find_result in re_include_output.finditer(include_terminal_output):
        result.append( (find_result.group('type'), find_result.group('name')) )
    return result



def parse_run(ghdl_output):
    """ Parse GHDL run output
    """

    ghdl_output_lines = ghdl_output.splitlines()
    lines_to_process = len(ghdl_output_lines) - 2

    # First line contains the top entity name, second contains the top entity arch
    current_line = 0
    unit = ''
    while unit != 'entity':
        entity_name, unit = get_name_and_unit(ghdl_output_lines[current_line])
        current_line += 1
    arch_name, unit = get_name_and_unit(ghdl_output_lines[current_line])
    current_line += 1


    # Create top representation
    top = Top(name='top')
    top.entity = Entity(name=entity_name, parent=top, indentation=TAB, arch=arch_name)


    # Get blocks by level of indentation
    current_unit = top.entity
    previous_indentation = TAB

    while current_line < lines_to_process:
        current_indentation = get_indentation(ghdl_output_lines[current_line])
        current_name, current_type = get_name_and_unit(ghdl_output_lines[current_line])


        # Add same level
        if current_indentation == previous_indentation:
            current_parent = current_unit.parent
        # Add inside previous
        elif current_indentation == previous_indentation + TAB:
            current_parent = current_unit
        # Search parent and add
        elif current_indentation < previous_indentation:
            current_parent = get_parent(current_unit, current_indentation)
        else:
            raise ValueError('Error processing indentation in line: ' + str(current_line + 1))


        # Entities
        if current_type == 'instance':
            current_unit = Instance(name=current_name, parent=current_parent, indentation=current_indentation)
        elif current_type == 'entity':
            current_unit = Entity(name=current_name, parent=current_parent, indentation=current_indentation)
        elif current_type == 'arch':
            current_unit.arch = current_name
            current_unit.indentation = current_indentation

        # Generates
        elif current_type in GENERATE_STATEMENTS:
            current_unit = Generate(name=current_name, parent=current_parent, indentation=current_indentation, value=get_generate_value(ghdl_output_lines[current_line]))

        # Packages
        elif current_type == 'package':
            top.packages.append(current_name)

        # else:
        #     raise ValueError('Error invalid unit type: ' + current_type)


        current_line += 1
        previous_indentation = current_indentation


    return top

