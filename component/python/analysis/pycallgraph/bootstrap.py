#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a git repository from the provided URL.

    This function clones a git repository from the given URL to the
    specified repository path.

    Args:
        url (str): The URL of the git repository to clone.

    Returns:
        bool: True if the cloning was successful, False otherwise.
    """

    r = subprocess.run(['git', 'clone', url, REPO_PATH])

    if r.returncode == 0:
        return True
    else:
        print("[COUT] Git clone error: Invalid argument to exit",
              file=sys.stderr)
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
    """Return the appropriate Python command based on the given version.

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
    """Initialize the environment by installing 'pycallgraph' package using pip
    for the specified version.

    Args:
        version (str): The version of Python for which 'pycallgraph' package needs to be
            installed.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pycallgraph'])


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
    path using the given Python version.

    Args:
        path (str): The path to the file containing the dependencies.
        version (str): The Python version to use for installation (default is 'py3k').

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
    specified in the given requirements file.

    Args:
        file_name (str): The path to the requirements file.
        version (str): The Python version to use with pip (default is 'py3k').

    Returns:
        bool: True if the installation is successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def pycallgraph(file_name, upload):
    """Generate a call graph using pycallgraph and upload it.

    This function generates a call graph for a specified file using
    pycallgraph and then uploads the generated graph.

    Args:
        file_name (str): The name of the file for which the call graph is to be generated.
        upload (str): The URL to which the call graph image will be uploaded.

    Returns:
        bool: True if the call graph generation and upload were successful, False
            otherwise.
    """

    r = subprocess.run(['pycallgraph', 'graphviz', '--',
                        '{}/{}'.format(REPO_PATH, file_name)])

    if r.returncode != 0:
        print("[COUT] pycallgraph error", file=sys.stderr)
        return False

    r1 = subprocess.run(['curl', '-XPUT', '-d', '@pycallgraph.png', upload])
    if r1.returncode != 0:
        print("[COUT] upload error", file=sys.stderr)
        return False
    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    If the 'CO_DATA' environment variable is not set, an empty dictionary is
    returned. The 'CO_DATA' string is split by spaces, and each key-value
    pair is extracted based on the format 'key=value'. Only key-value pairs
    with keys in the 'validate' list are considered valid.

    Returns:
        dict: A dictionary containing valid key-value pairs extracted from 'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-file', 'upload', 'version']
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
    """Main function to process input arguments, validate version, initialize
    environment,
    clone git repository, setup packages, install requirements, and generate
    pycallgraph.
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

    upload = argv.get('upload')
    if not upload:
        print("[COUT] The upload value is null", file=sys.stderr)
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

    out = pycallgraph(entry_file, upload)
    print()

    if out:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
