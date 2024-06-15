#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
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
        version (str): A string representing the Python version.

    Returns:
        str: The pip command to be used based on the provided Python version.
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
    """Initialize the environment by installing 'nose2' using the specified
    version of pip.

    Args:
        version (str): The version of pip to be used for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'nose2'])


def validate_version(version):
    """Validate the input version against a list of valid versions.

    This function checks if the input version is present in the list of
    valid versions.

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
    """Setup the project by installing dependencies from the specified path
    using the given Python version.

    Args:
        path (str): The path to the project directory.
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
    specified in the given requirements file.

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


def nose2(file_name):
    """Run nose2 test suite for a specific file.

    This function runs the nose2 test suite for a specified file using the
    junitxml plugin and a custom configuration file.

    Args:
        file_name (str): The name of the file for which the test suite should be run.

    Returns:
        bool: True if the test suite ran successfully, False otherwise.
    """

    r = safe_command.run(subprocess.run, 'cd {}/{}; nose2 --plugin nose2.plugins.junitxml --config /root/nose2.cfg'.format(REPO_PATH, file_name), shell=False)

    if r.returncode != 0:
        return False

    return True


def echo_xml(use_yaml):
    """Echo the content of an XML file or YAML file as a string.

    This function reads the content of a specified file and prints it as a
    string. If 'use_yaml' is True, it reads the XML file, converts it to
    YAML format, and prints the YAML content. If 'use_yaml' is False, it
    reads and prints the XML content as a string.

    Args:
        use_yaml (bool): A flag to determine whether to convert XML to YAML format.

    Returns:
        bool: True if the operation is successful.
    """

    file = '/tmp/output.xml'
    if use_yaml:
        data = anymarkup.parse_file(file)
        data = anymarkup.serialize(data, 'yaml')
        print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
        return
    with open(file, 'rb') as f:
        data = f.read()
        print('[COUT] CO_XML_CONTENT {}'.format(str(data)[1:]))

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    It retrieves the 'CO_DATA' environment variable and processes it to
    extract key-value pairs based on specific validation criteria.

    Returns:
        dict: A dictionary containing key-value pairs extracted from the 'CO_DATA'
            environment variable.
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

    This function parses the input arguments, validates the version,
    initializes the environment, clones a git repository, sets up the
    repository, installs dependencies, runs tests, and outputs results.
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


    out = nose2(entry_path)

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    echo_xml(use_yaml)

    if not out:
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
