from re import compile



###############################################################################
# REGULAR EXPRESSIONS
###############################################################################

re_find_name_and_unit = compile('(?P<name>[\w|\(|\)|\.]+)\s\[(?P<unit>(if-generate|for-generate|instance|arch|entity|package)).*\]')

re_find_value = compile('(?P<value>(true|false))\]')

re_find_indentation = compile('(?P<indentation>\W*)\w')

re_index = compile('\((?P<index>\d+)\)')

re_include_output = compile('(?P<type>(entity|package))\s(?P<name>\w+)')

re_vend_srcs = compile('SourceDirectories\[(?P<name>\w+)\]\s*=\s*"(?P<path>(\w|\/|\.)+)')
