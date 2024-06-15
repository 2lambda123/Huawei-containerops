#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a git repository from the provided URL.

    This function clones a git repository from the specified URL to the
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
        str: The appropriate pip command based on the provided Python version.
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

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'memory_profiler',
        'psutil', 'pyyaml'])


def validate_version(version):
    """Validate the input version against a list of valid versions.

    Args:
        version (str): The version string to be validated.

    Returns:
        bool: True if the version is valid, False otherwise.
    """

    valid_version = ['python', 'python2', 'python3', 'py3k']
    if version not in valid_version:
        print("[COUT] Check version failed: the valid version is {}".format(valid_version), file=sys.stderr)
        return False

    return True


def setup(path, version='py3k'):
    """Set up the environment by installing dependencies from the specified
    path.

    This function changes the directory to the specified path, then runs the
    installation command using the provided Python version.

    Args:
        path (str): The path where the dependencies are located.
        version (str): The Python version to use for installation (default is 'py3k').

    Returns:
        bool: True if the installation was successful, False otherwise.
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


def memory_profiler(file_name, version='py3k', use_yaml = False):
    """Run memory profiler on a Python script.

    This function runs the memory profiler on the specified Python script
    using the specified Python version. It also provides an option to output
    the results in YAML format.

    Args:
        file_name (str): The name of the Python script file to profile.
        version (str?): The Python version to use for profiling (default is 'py3k').
        use_yaml (bool?): Flag to indicate whether to output results in YAML format (default is
            False).

    Returns:
        bool: True if the memory profiler ran successfully, False otherwise.
    """

    r = safe_command.run(subprocess.run, [get_python_cmd(version), '/root/memory_profiler.py',
                        '--yaml', str(use_yaml),
                        os.path.join(REPO_PATH, file_name)])

    passed = True
    if (r.returncode != 0):
        passed = False

    return passed


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs to
    return as a dictionary.

    If 'CO_DATA' is not set or empty, an empty dictionary is returned.

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
    install dependencies, run memory profiler, and print the result.
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

    out = memory_profiler(entry_file, version, use_yaml)

    if out:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
