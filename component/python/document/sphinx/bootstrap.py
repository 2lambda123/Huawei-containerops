#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
import json
import anymarkup
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
            Should be either 'py3k' or 'python3'.

    Returns:
        str: The appropriate pip command based on the provided Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def get_python_cmd(version):
    """Determine the appropriate Python command based on the given version.

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
    """Initialize the environment by installing Sphinx package using pip.

    This function installs the Sphinx package using the specified version of
    pip command.

    Args:
        version (str): The version of pip command to be used for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'sphinx'])


def validate_version(version):
    """Validate the input version against a list of valid versions.

    It checks if the input version is present in the list of valid versions.

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
    """Set up the environment by installing dependencies from a given path.

    This function sets up the environment by running the installation
    command for the specified path and Python version.

    Args:
        path (str): The path to the directory containing the dependencies.
        version (str): The Python version to use for installation (default is 'py3k').

    Returns:
        bool: True if the installation is successful, False otherwise.
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
        bool: True if the installation is successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def sphinx(dir_name):
    """Run Sphinx documentation generation for the specified directory.

    This function runs the Sphinx documentation generation process for the
    specified directory by executing the 'make json' command.

    Args:
        dir_name (str): The name of the directory where Sphinx documentation will be generated.

    Returns:
        bool: True if the Sphinx documentation generation was successful, False
            otherwise.
    """

    r = safe_command.run(subprocess.run, 'cd {}/{}; make json'.format(REPO_PATH, dir_name), shell=False)

    if r.returncode != 0:
        print("[COUT] sphinx error", file=sys.stderr)
        return False

    return True


def echo_json(dir_name, use_yaml):
    """Echo the content of JSON files in a specified directory.

    This function walks through the specified directory and its
    subdirectories, reads JSON files, and prints their content in either
    JSON or YAML format.

    Args:
        dir_name (str): The name of the directory to search for JSON files.
        use_yaml (bool): A flag to determine whether to print content in YAML format.

    Returns:
        bool: True if the function executes successfully.
    """

    for root, dirs, files in os.walk('{}/{}/_build/json'.format(REPO_PATH, dir_name)):
        for file_name in files:
            if file_name.endswith('.fjson'):
                data = json.load(open(os.path.join(root, file_name)))
                if use_yaml:
                    data = anymarkup.serialize(data, 'yaml')
                    print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
                else:
                    print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(data)))

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    If the 'CO_DATA' environment variable is not set or empty, an empty
    dictionary is returned. The function iterates over the space-separated
    key-value pairs in 'CO_DATA', validates each pair, and constructs a
    dictionary with valid key-value pairs.

    Returns:
        dict: A dictionary containing key-value pairs extracted from 'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-path', 'version', 'out-put-type']
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
    """Main function to perform a series of tasks based on input arguments.

    This function takes input arguments, validates them, initializes the
    environment, clones a git repository, sets up the repository, installs
    dependencies, generates documentation using Sphinx, and outputs the
    result in JSON or YAML format.
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

    entry_path = argv.get('entry-path')
    if not entry_path:
        print("[COUT] The entry-path value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    if not git_clone(git_url):
        return

    for file_name in glob.glob('{}/setup.py'.format(REPO_PATH)):
        setup(file_name, version)

    for file_name in glob.glob('{}/*/setup.py'.format(REPO_PATH)):
        setup(file_name, version)

    for file_name in glob.glob('{}/requirements.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    for file_name in glob.glob('{}/*/requirements.txt'.format(REPO_PATH)):
        pip_install(file_name, version)


    if not sphinx(entry_path):
        print("[COUT] CO_RESULT = false")
        return

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    if not echo_json(entry_path, use_yaml):
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
