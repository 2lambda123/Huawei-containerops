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
            Accepted values are 'py3k' or 'python3'.

    Returns:
        str: The appropriate pip command based on the provided Python version.
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
    """Initialize the environment by installing necessary packages using pip.

    This function installs 'green' and 'coverage' packages using the
    specified version of pip command.

    Args:
        version (str): The version of pip command to be used for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'green', 'coverage'])


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
    """Setup the environment by installing dependencies from the specified
    path.

    Args:
        path (str): The path to the directory containing the dependencies.
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


def get_dir_name(dir_name):
    """Returns the directory path based on the input directory name.

    If the input directory name is not empty and not equal to '.', the
    function appends it to the REPO_PATH. If the input directory name is
    empty or '.', the function returns the REPO_PATH directly.

    Args:
        dir_name (str): The input directory name.

    Returns:
        str: The directory path based on the input directory name.
    """

    if dir_name and dir_name != '.':
        dir_name = '{}/{}'.format(REPO_PATH, dir_name)
    else:
        dir_name = REPO_PATH

    return dir_name


def green(dir_name):
    """Run 'green -r' command in the specified directory.

    This function runs the 'green -r' command in the specified directory and
    returns True if the command is executed successfully, otherwise returns
    False.

    Args:
        dir_name (str): The directory path where the 'green -r' command will be executed.

    Returns:
        bool: True if the command is executed successfully, False otherwise.
    """

    r = safe_command.run(subprocess.run, 'cd {}; green -r'.format(get_dir_name(dir_name)), shell=False)

    if r.returncode != 0:
        return False

    return True


def echo_json(dir_name, use_yaml):
    """Print the content of a JSON or YAML file.

    This function reads the content of a file located at the specified
    directory, extracts the JSON data, and then prints the data in either
    JSON or YAML format based on the 'use_yaml' parameter.

    Args:
        dir_name (str): The directory name where the file is located.
        use_yaml (bool): A flag indicating whether to output the data in YAML format.
    """

    file_name = '{}/.coverage'.format(get_dir_name(dir_name))
    data = open(file_name).read()
    idx = data.find('{')
    data = data[idx:]
    data = json.loads(data)
    if use_yaml:
        data = anymarkup.serialize(data, 'yaml')
        print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
    else:
        print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(data)))


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specified validation criteria.

    If the 'CO_DATA' environment variable is not set, an empty dictionary is
    returned. The 'CO_DATA' string is split by spaces, and each key-value
    pair is extracted based on the format 'key=value'. Only key-value pairs
    with keys in the validation list ['git-url', 'entry-path', 'version',
    'out-put-type'] are considered. Any key-value pair not following the
    specified format or having an invalid key is ignored.

    Returns:
        dict: A dictionary containing the extracted key-value pairs from 'CO_DATA'.
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

    This function parses input arguments, validates the version, initializes
    the environment, clones a git repository, sets up the repository,
    installs dependencies, and outputs the result.
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

    for file_name in glob.glob('{}/requirements_dev.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    for file_name in glob.glob('{}/*/requirements_dev.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    out = green(entry_path)

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    echo_json(entry_path, use_yaml)

    if not out:
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
