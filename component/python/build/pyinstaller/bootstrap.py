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
        bool: True if the cloning is successful, False otherwise.
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
        version (str): The Python version for which to determine the pip command. Should be
            'py3k' or 'python3'.

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
    """Initialize the environment by installing PyInstaller using the specified
    version of pip.

    Args:
        version (str): The version of pip to be used for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pyinstaller'])


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
    """Setup the environment by installing dependencies from the specified path
    using the given Python version.

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


def upload_file(upload):
    """Upload a file using curl command.

    This function uploads a file to a specified location using the curl
    command.

    Args:
        upload (str): The URL where the file will be uploaded.

    Returns:
        bool: True if the file was uploaded successfully, False otherwise.
    """

    r1 = subprocess.run(['curl', '-XPUT', '-d', '@/tmp/output.tar.bz2', upload])
    if r1.returncode != 0:
        print("[COUT] upload error", file=sys.stderr)
        return False
    print()
    return True


def pyinstaller(file_name):
    """Run PyInstaller to convert a Python script into a standalone executable.

    Args:
        file_name (str): The name of the Python script file to convert.

    Returns:
        bool: True if PyInstaller ran successfully, False otherwise.
    """

    r = subprocess.run(['pyinstaller', '{}/{}'.format(REPO_PATH, file_name)])

    if r.returncode != 0:
        print("[COUT] pyinstaller error", file=sys.stderr)
        return False

    return True


def compress():
    """Compress the files in the 'dist' directory into a tar.bz2 archive.

    It compresses the files in the 'dist' directory into a tar.bz2 archive
    located at '/tmp/output.tar.bz2'.

    Returns:
        bool: True if compression is successful, False otherwise.
    """

    r = subprocess.run('cd dist; tar cjvf /tmp/output.tar.bz2 .', shell=True)

    if r.returncode != 0:
        print("[COUT] compress error", file=sys.stderr)
        return False

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' to extract and validate
    specific arguments.

    It retrieves the 'CO_DATA' environment variable and parses it to extract
    key-value pairs representing arguments. The function validates the
    arguments against a predefined list and returns a dictionary of valid
    arguments.

    Returns:
        dict: A dictionary containing valid arguments extracted from the 'CO_DATA'
            environment variable.
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
    """Main function to perform a series of tasks for setting up and deploying
    a Python project.
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

    for file_name in glob.glob('{}/setup.py'.format(REPO_PATH)):
        setup(file_name, version)

    for file_name in glob.glob('{}/*/setup.py'.format(REPO_PATH)):
        setup(file_name, version)

    for file_name in glob.glob('{}/requirements.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    for file_name in glob.glob('{}/*/requirements.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    if not pyinstaller(entry_file):
        print("[COUT] CO_RESULT = false")
        return

    if not compress():
        print("[COUT] CO_RESULT = false")
        return

    if not upload_file(upload):
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
