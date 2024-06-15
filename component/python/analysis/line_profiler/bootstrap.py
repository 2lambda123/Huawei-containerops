#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
import json
import line_profiler as profiler
import linecache
import inspect
import yaml
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a git repository from the provided URL.

    This function clones a git repository from the given URL to the
    predefined REPO_PATH.

    Args:
        url (str): The URL of the git repository to clone.

    Returns:
        bool: True if the cloning was successful, False otherwise.
    """

    r = subprocess.run(['git', 'clone', url, REPO_PATH])

    if (r.returncode == 0):
        return True
    else:
        print("[COUT] Git clone error: Invalid argument to exit", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return False


def get_pip_cmd(version):
    """Determine the appropriate pip command based on the Python version
    provided.

    Args:
        version (str): The Python version for which to determine the pip command.

    Returns:
        str: The appropriate pip command based on the Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def get_python_cmd(version):
    """Return the appropriate Python command based on the specified version.

    This function takes a version string as input and returns the
    corresponding Python command.

    Args:
        version (str): A string representing the Python version ('py3k' or 'python3').

    Returns:
        str: The Python command based on the input version.
    """

    if version == 'py3k' or version == 'python3':
        return 'python3'

    return 'python'


def init_env(version):
    """Initialize the environment by installing necessary packages for the
    specified Python version.

    Args:
        version (str): The Python version for which the environment needs to be initialized.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'cython', 'line_profiler'])


def validate_version(version):
    """Validate the input version against a list of valid versions.

    Args:
        version (str): The version to be validated.

    Returns:
        bool: True if the version is valid, False otherwise.
    """

    valid_version = ['python', 'python2', 'python3', 'py3k']
    if version not in valid_version:
        print("[COUT] Check version failed: the valid version is {}".format(valid_version), file=sys.stderr)
        return False

    return True


def setup(path, version='py3k'):
    """Setup the environment by installing dependencies from the given path
    using the specified Python version.

    Args:
        path (str): The path to the file containing the dependencies.
        version (str?): The Python version to use for installation. Defaults to 'py3k'.

    Returns:
        bool: True if the setup is successful, False otherwise.
    """

    file_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    r = safe_command.run(subprocess.run, 'cd {}; {} {} install'.format(dir_name, get_python_cmd(version), file_name),
                       shell=False)

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def pip_install(file_name, version='py3k'):
    """Install dependencies from a requirements file using pip.

    This function runs the pip install command to install dependencies
    listed in the specified requirements file.

    Args:
        file_name (str): The path to the requirements file.
        version (str): The Python version to use with pip (default is 'py3k').

    Returns:
        bool: True if the installation was successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def show_json(stats, unit):
    """    Show text for the given timings.

    This function generates a dictionary containing information about the
    timings of functions.

    Args:
        stats (dict): A dictionary containing timing statistics for functions.
        unit (float): The unit of time used for timings.

    Returns:
        dict: A dictionary containing information about the timings of functions.
    """
    retval = {}
    retval['Timer unit'] = '%g s' % unit
    retval['functions'] = []
    for (fn, lineno, name), timings in sorted(stats.items()):
        func = show_func(fn, lineno, name, stats[fn, lineno, name], unit)
        if func:
            retval['functions'].append(func)

    return retval

def show_func(filename, start_lineno, func_name, timings, unit):
    """    Show results for a single function.

    This function takes in the filename, starting line number, function
    name, timings, and unit to display results for a single function. It
    calculates the total time, retrieves relevant lines of code, and formats
    the output for display.

    Args:
        filename (str): The name of the file containing the function.
        start_lineno (int): The starting line number of the function.
        func_name (str): The name of the function.
        timings (list): A list of tuples containing line number, number of hits, and time taken.
        unit (float): The unit of time for calculations.

    Returns:
        dict: A dictionary containing the results for the function, including total
            time, file name, function name, line details, and more.
    """

    d = {}
    total_time = 0.0
    linenos = []
    for lineno, nhits, time in timings:
        total_time += time
        linenos.append(lineno)

    if total_time == 0:
        return False

    retval = {}

    retval['Total time'] = "%g s" % (total_time * unit)
    if os.path.exists(filename) or filename.startswith("<ipython-input-"):
        retval['File'] = filename
        retval['Function'] = '%s at line %s' % (func_name, start_lineno)
        if os.path.exists(filename):
            # Clear the cache to ensure that we get up-to-date results.
            linecache.clearcache()
        all_lines = linecache.getlines(filename)
        sublines = inspect.getblock(all_lines[start_lineno-1:])
    else:
        # Fake empty lines so we can see the timings, if not the code.
        nlines = max(linenos) - min(min(linenos), start_lineno) + 1
        sublines = [''] * nlines

    for lineno, nhits, time in timings:
        d[lineno] = (nhits, time, '%5.1f' % (float(time) / nhits),
            '%5.1f' % (100*time / total_time))
    linenos = range(start_lineno, start_lineno + len(sublines))
    empty = ('', '', '', '')
    lines = []
    for lineno, line in zip(linenos, sublines):
        nhits, time, per_hit, percent = d.get(lineno, empty)
        line = {
                'Line #': lineno,
                'Hits': nhits,
                'Time': time,
                'Per Hit': per_hit,
                '% Time': percent,
                'Line Contents': line.rstrip('\n').rstrip('\r')
                }
        lines.append(line)

    retval['lines'] = lines
    return retval

def line_profiler(file_name, use_yaml):
    """Profile a Python script using line-by-line profiling.

    This function runs the 'kernprof' command to perform line-by-line
    profiling on the specified Python script. It then loads the profiling
    statistics and displays the timings in either JSON or YAML format based
    on the 'use_yaml' flag.

    Args:
        file_name (str): The name of the Python script to be profiled.
        use_yaml (bool): A flag indicating whether to output the profiling results in YAML
            format.

    Returns:
        bool: True if the profiling process completed successfully, False otherwise.
    """

    r = subprocess.run(['kernprof', '-l', os.path.join(REPO_PATH, file_name)], stdout=subprocess.PIPE)

    passed = True
    if (r.returncode != 0):
        passed = False

    st = profiler.load_stats('{}/{}.lprof'.format(REPO_PATH, file_name))
    out = show_json(st.timings, st.unit)
    if use_yaml:
        out = bytes(yaml.safe_dump(out), 'utf-8')
        print('[COUT] CO_YAML_CONTENT {}'.format(str(out)[1:]))
    else:
        print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(out)))

    return passed


def trim_repo_path(n):
    """Trims the repository path from the given string.

    This function takes a string and removes the repository path prefix from
    it.

    Args:
        n (str): The input string containing the full path.

    Returns:
        str: The trimmed string without the repository path prefix.
    """

    return n[len(REPO_PATH) + 1:]


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs as
    arguments.

    If 'CO_DATA' is not set or empty, an empty dictionary is returned. The
    function iterates over space-separated key-value pairs in 'CO_DATA',
    validates each key against a predefined list, and constructs a
    dictionary with valid key-value pairs.

    Returns:
        dict: A dictionary containing key-value pairs extracted from 'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-file', 'version', 'out-put-type']
    ret = {}
    for s in data.split(' '):
        s = s.strip()
        if not s:
            continue
        arg = s.split('=')
        if len(arg) < 2:
            print('[COUT] Unknown Parameter: [{}]'.format(s))
            continue

        if arg[0] not in validate:
            print('[COUT] Unknown Parameter: [{}]'.format(s))
            continue

        ret[arg[0]] = arg[1]

    return ret


def main():
    """Main function to process input arguments, clone git repository, set up
    environment,
    install dependencies, and run line profiler on the specified entry file.
    """

    argv = parse_argument()
    git_url = argv.get('git-url')
    if not git_url:
        print("[COUT] The git-url value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    version = argv.get('version', 'py3k')

    if not validate_version(version):
        print("[COUT] CO_RESULT = false")
        return

    init_env(version)

    entry_file = argv.get('entry-file')
    if not entry_file:
        print("[COUT] The entry-file value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    if not git_clone(git_url):
        return

    for file_name in glob.glob('./*/setup.py'):
        setup(file_name, version)

    for file_name in glob.glob('./*/*/setup.py'):
        setup(file_name, version)

    for file_name in glob.glob('./*/requirements.txt'):
        pip_install(file_name, version)

    for file_name in glob.glob('./*/*/requirements.txt'):
        pip_install(file_name, version)

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    out = line_profiler(entry_file, use_yaml)

    if out:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
