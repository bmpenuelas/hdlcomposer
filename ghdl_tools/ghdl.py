from   os import getcwd, mkdir
from   os.path import (normpath, join, abspath, exists, dirname, isabs, basename)
from   sys import stdout
from   shutil import rmtree
from   platform import system
from   json import (dump, load)
from   math import ceil

from   ghdl_tools.utils import (run_console_command, get_dirs_containing_files,
                                save_txt, get_filepaths_recursive,
                                gtkwave_open_wave)
from   ghdl_tools.regular_expressions import re_vend_srcs
from   ghdl_tools.parse import parse, parse_included




###############################################################################
# GHDL COMMAND WRAPPERS
###############################################################################

# Run once per installation and reuse the compiled result
def compile_vendor(vendor_name, output_path, vendor_install_path, ghdl_install_path,
                   standard='93', recompile=False, verbose=False):
    if standard == '93':
        vhdl_standard = 'VHDL93'
    elif standard == '2008':
        vhdl_standard = 'VHDL2008'
    else:
        raise ValueError('Invalid VHDL standard. Valid values are 93, 2008')


    output_path_norm = abspath(output_path)
    if (not recompile) and get_dirs_containing_files(output_path_norm, extension='.cf'):
        message = vendor_name + ' libraries found, not recompiling'
        if verbose:
            stdout.write(message + '\n')
        return 2, message
    else:
        if verbose:
            stdout.write('Compiling ' + vendor_name + ' libraries...\n')

    with open(join(ghdl_install_path, 'lib/vendors/config.sh'), 'r', encoding='utf-8') as settings_file:
        srcs_dir = {re_vend_srcs.search(line).group('name').lower(): re_vend_srcs.search(line).group('path')
                    for line in settings_file.readlines() if re_vend_srcs.search(line)}
    vendor_sources_dir = join(normpath(vendor_install_path), normpath(srcs_dir[vendor_name.lower().replace('-','')]))


    OS = system()
    if OS == 'Windows':
        compile_vendor_command = \
            'powershell.exe -Command "' + \
            normpath( join( join(ghdl_install_path, 'lib/vendors'), ('compile-' + vendor_name + '.ps1') ) ) + \
            ' -Source ' + vendor_sources_dir + \
            ' -' + vhdl_standard + \
            ' -SuppressWarnings' + \
            ' -Output ' + output_path_norm + \
            ' -All -GHDL ' + normpath( join(ghdl_install_path, 'bin') ) + \
            '"'
    elif (OS == 'Linux') or (OS == 'Darwin'):
        compile_vendor_command = \
            normpath( join( join(ghdl_install_path, 'lib/vendors'), ('compile-' + vendor_name + '.sh') ) ) + \
            ' -Source ' + vendor_sources_dir + \
            ' -' + vhdl_standard + \
            ' -SuppressWarnings' + \
            ' -Output ' + output_path_norm + \
            ' -All -GHDL ' + normpath( join(ghdl_install_path, 'bin') )
    else:
        raise ValueError('Automatic vendor libs compilation is only available in Linux, Mac and Windows')

    return run_console_command(compile_vendor_command)



# Run to import and to get the entity and architectures present in the file
def import_file(file_path, workdir):
    file_path = normpath(file_path)
    workdir = normpath(workdir)
    import_command = \
        'ghdl -i -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + \
        ' ' + file_path
    command_run_result = run_console_command(import_command)
    error = command_run_result[0]
    terminal_output = command_run_result[1]
    units_description = parse_included(terminal_output)
    return error, terminal_output, import_command, units_description



# Compile the imported files, requires previous import_file()
def make_entity(entity_name, workdir, additional_libs):
    workdir = normpath(workdir)
    additional_libs = ' -P' + ' -P'.join(additional_libs) if additional_libs else ''
    make_command = \
        'ghdl -m -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + \
        additional_libs + \
        ' ' + entity_name
    return run_console_command(make_command) + (make_command,)



# Generate a (large) XML representation of the file
def dump_xml_file(file_path, workdir, additional_libs, output_file_path):
    additional_libs = ' -P ' + ' -P '.join(additional_libs) if additional_libs else ''
    output_file_path = abspath(output_file_path)
    dump_xml_command = \
        'ghdl --file-to-xml -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + \
        ' ' + file_path
    error, xml = run_console_command(dump_xml_command)
    if not error:
        save_txt(xml, output_file_path)
    return error, output_file_path



# Generate HTML navigable HTML tree of the provided files. Requires previous make_entity()
def generate_cross_references_html(file_path, workdir, additional_libs, output_path=''):
    additional_libs = ' -P ' + ' -P '.join(additional_libs) if additional_libs else ''
    if output_path:
        output_path = abspath(output_path)
        if not exists(output_path):
            mkdir(output_path)

    gen_cross_refs_command = \
        'ghdl --xref-html -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + \
        ' --format=css' + \
        (' -o ' + output_path if output_path else '') + \
        ' ' + file_path
    return run_console_command(gen_cross_refs_command)



def analyze_file(file_path, workdir, additional_libs):
    additional_libs = ' -P ' + ' -P '.join(additional_libs) if additional_libs else ''
    analyze_command = \
        'ghdl -a -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + \
        additional_libs + \
        ' ' + file_path
    return run_console_command(analyze_command)



def elaborate_entity(entity_name, workdir):
    elaborate_command = \
        'ghdl -e -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + \
        ' ' + entity_name
    return run_console_command(elaborate_command)



def run_tb(testbench_name, workdir, run_time='1us'):
    workdir = normpath(workdir)
    run_command = \
        'ghdl -r -v --ieee=synopsys -fexplicit' + \
        ' --workdir=' + workdir + ' ' + \
        testbench_name + \
        ' --wave=' + join(workdir, (testbench_name + '.ghw')) + \
        (' --stop-time=' + run_time if (run_time and not run_time == '0') else ' --no-run --disp-tree=inst')
    return run_console_command(run_command)



class SetExt(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def append(self, data):
        self.update(data)


###############################################################################
# GHDL
###############################################################################

class GHDL():

    def __init__(self, verbose=False, install_path=None, vhdl_standard=None,
                 work_dir_path=None, compiled_libs_paths=None, always_reimport=True,
                 sources_directories=None, sources_paths=None, exclude_files=None,
                 testbench=None, waves_dir=''):
        self.verbose = verbose
        self.vhdl_standard = vhdl_standard or '93'
        self.work_dir_path = normpath(work_dir_path) if work_dir_path else join(getcwd(), normpath('./work/'))

        if compiled_libs_paths:
            self.compiled_libs_paths = SetExt()
            self.add_compiled_libs(compiled_libs_paths)
        else:
            self.compiled_libs_paths = SetExt([abspath('./compiled')])

        self.load_config_from_file()
        if install_path:
            self.install_path = install_path
        elif exists('C:/GHDL'):
            self.install_path = 'C:/GHDL'

        self.always_reimport = always_reimport
        self.exclude_files = exclude_files or []
        self.sources_paths = SetExt(sources_paths) if sources_paths else SetExt()
        self._sources_directories = set()
        self.sources_directories = sources_directories or [getcwd()]
        self.testbench = testbench if isinstance(testbench, list) else ([testbench] if testbench else [])
        self.waves_dir = normpath(waves_dir) if waves_dir else None



    @property
    def install_path(self):
        if not self.config['install_path']:
            self.load_config_from_file()
        return self.config['install_path']

    @install_path.setter
    def install_path(self, val):
        self.config['install_path'] = val
        self.save_config_to_file()



    @property
    def sources_directories(self):
        return self._sources_directories

    @sources_directories.setter
    def sources_directories(self, val):
        self._sources_directories = self._sources_directories.update(val) if self._sources_directories else set(val)
        self.add_sources_from_dir(val, exclude_files=self.exclude_files)



    def __repr__(self):
        return 'GHDL wrapper and configuration'



    def __str__(self):
        return 'GHDL VHDL ' + self.vhdl_standard



    def load_config_from_file(self):
        try:
            with open(join(self.work_dir_path, 'config')) as infile:
                self.config = load(infile)
        except FileNotFoundError:
            self.config = {
                'install_path': '',
                'imported_entities': {},
                'imported_packages': {},
            }
            self.save_config_to_file()



    def save_config_to_file(self):
        try:
            with open(join(self.work_dir_path, 'config'), 'w') as outfile:
                dump(self.config, outfile)
        except FileNotFoundError:
            mkdir(self.work_dir_path)
            with open(join(self.work_dir_path, 'config'), 'w') as outfile:
                dump(self.config, outfile)



    def add_compiled_libs(self, directory_paths):
        if not isinstance(directory_paths, list):
            directory_paths = [directory_paths]
        for directory_path in directory_paths:
            self.compiled_libs_paths.update(get_dirs_containing_files(directory_path, extension='.cf'))



    def compile_vendor(self, vendor_name, vendor_install_path, output_path='./compiled/vendor', recompile=False):
        output_path = join(normpath(output_path), vendor_name)
        if not self.install_path:
            raise ValueError('compile_vendor requires GHDL install_path')

        command_run_result = compile_vendor(
            vendor_name,
            output_path,
            vendor_install_path,
            self.install_path,
            self.vhdl_standard,
            recompile,
            self.verbose
        )
        if command_run_result[0] == 0 and self.verbose:
            stdout.write('Finished compilation of ' + vendor_name + '\n')

        self.add_compiled_libs(output_path)
        return command_run_result



    def add_sources_from_dir(self, sources_directories, extensions=['.vhd', '.vhdl'],
                             include_files=[], exclude_files=[]):
        vhd_paths = set()
        for src_folder in sources_directories:
            vhd_paths.update( get_filepaths_recursive(src_folder, extensions, include_files, exclude_files) )
        if self.verbose:
            stdout.write('Found ' + str(len(vhd_paths)) + ' VHDL files\n')
        self.sources_paths.update(vhd_paths)



    def import_file(self, file_path):
        error, terminal_output, import_command, units_description = import_file(file_path, self.work_dir_path)
        if not error:
            for unit_description in units_description:
                if unit_description[0] == 'entity':
                    self.config['imported_entities'][unit_description[1]] = file_path
                    self.save_config_to_file()
                elif unit_description[0] == 'package':
                    self.config['imported_packages'][unit_description[1]] = file_path
                    self.save_config_to_file()
        return error, terminal_output, import_command, units_description



    def make_entity(self, entity):
        return make_entity(entity, self.work_dir_path, self.compiled_libs_paths)



    def dump_xml_file(self, file_path, output_file_path):
        return dump_xml_file(file_path, self.work_dir_path, self.compiled_libs_paths, output_file_path)



    def generate_cross_references_html(self, file_path, output_path=''):
        return generate_cross_references_html(file_path, self.work_dir_path, self.compiled_libs_paths, output_path)



    def run_tb(self, entity, run_time):
        return run_tb(entity, self.work_dir_path, run_time)



    def parse_entity(self, entity):
        error, terminal_output = run_tb(entity, self.work_dir_path, 0)
        return parse(terminal_output)



    def open_waves(self, entity):
        self.load_config_from_file()

        entity_dir = dirname(self.config['imported_entities'][entity.lower()])
        if self.waves_dir:
            if isabs(normpath(self.waves_dir)):
                testbench_waves_dir = normpath(self.waves_dir)
            else:
                testbench_waves_dir = join(entity_dir, normpath(self.waves_dir))
        else:
            testbench_waves_dir = join(entity_dir, normpath('./waves/'))

        found_wave_files = get_filepaths_recursive(testbench_waves_dir, extensions=['.gtkw'])

        ghw_path = join(self.work_dir_path, (entity + '.ghw'))
        if found_wave_files:
            if self.verbose:
                stdout.write( ' ' * 2 + 'Found ' + str(len(found_wave_files)) +
                              ' wave file' + ('s' if len(found_wave_files) > 1 else '') + '\n')
            for gtkw_file in found_wave_files:
                gtkwave_open_wave(ghw_path, gtkw_file)
                if self.verbose:
                    stdout.write(' ' * 4 + 'Opening ' + basename(gtkw_file) + '\n')
        else:
            gtkwave_open_wave(ghw_path)



    def import_sources(self):
        has_to_import = True
        if exists(self.work_dir_path):
            if not self.always_reimport and get_dirs_containing_files(self.work_dir_path, extension='.cf'):
                has_to_import = False
                if self.verbose:
                    stdout.write('Not reimporting sources\n')
                return
            else:
                # Cleanup work dir
                rmtree(self.work_dir_path)
                mkdir(self.work_dir_path)
        else:
            mkdir(self.work_dir_path)

        if self.verbose:
            stdout.write('Importing included sources...\n')
        imported = 0
        previous_len = 0
        for file_path in self.sources_paths:
            import_error, terminal_output, import_command, units_description = self.import_file(file_path)

            if import_error:
                stdout.write('\nERROR Importing ' + file_path + terminal_output + '\n' +
                             'For more details, you can run:\n' + import_command + '\n')
            else:
                if self.verbose:
                    # Progress bar
                    imported += 1
                    i = ceil(imported * 20 / len(self.sources_paths))
                    stdout.write('\r')
                    stdout.write(' ' * 2 + '[%-20s] %d%% ' % ('='*i, imported / len(self.sources_paths) * 100))
                    imported_message = 'Imported ' + ' '.join([unit[1] for unit in units_description])
                    stdout.write(imported_message)
                    current_len = len(imported_message)
                    stdout.write(' ' * ((previous_len - current_len) if previous_len > current_len else 0))
                    previous_len = current_len
            if self.verbose:
                stdout.flush()
        if self.verbose:
            stdout.write('\n')



    def parse(self, show_output=False):
        result = []
        for entity in self.testbench:
            result.append(self.parse_entity(entity))
            if show_output:
                stdout.write('* ' + entity.upper() + ' TREE:\n')
                result[-1].print_children()
            stdout.write('\n')

        return result

        


    def run(self, run_time=None, open_waves=True):
        run_time = run_time or '1us'

        # Import
        self.import_sources()

        # Make
        for entity in self.testbench:
            if self.verbose:
                stdout.write('Make ' + entity + '\n')
            make_error, make_terminal_output, make_command = self.make_entity(entity)

            # Run
            if not make_error:
                if self.verbose:
                    stdout.write('Running testbench ' + entity + ' ' + (run_time or '') + '...\n')

                error_occurred, run_terminal_output = self.run_tb(entity, run_time)

                if error_occurred:
                    stdout.write('ERROR Running testbench ' + entity + '\n')
                    stdout.write(run_terminal_output + '\n')

                # Open wave files
                if not error_occurred and open_waves:
                    if self.verbose:
                        stdout.write('Opening ' + entity + ' wave files\n')
                    self.open_waves(entity)

            else:
                stdout.write('ERROR Make ' + entity + '\n')
                if make_terminal_output:
                    stdout.write(make_terminal_output + '\n')
                stdout.write('For more details, you can run:' + '\n' + make_command + '\n')
