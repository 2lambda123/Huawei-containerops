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
    predefined REPO_PATH.

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


def setup(path):
    """Set up the environment by installing dependencies from the specified
    path.

    Args:
        path (str): The path to the file containing the dependencies.

    Returns:
        bool: True if the setup is successful, False otherwise.
    """

    file_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    r = safe_command.run(subprocess.run, 'cd {}; python3 {} install'.format(dir_name, file_name),
                       shell=False)

    if r.returncode != 0:
        print("[COUT] install dependences failed: {}".format(path), file=sys.stderr)
        return False

    return True


def pip_install(file_name):
    """Install Python packages listed in a requirements file using pip3.

    This function runs 'pip3 install -r <file_name>' command to install
    packages specified in the requirements file.

    Args:
        file_name (str): The path to the requirements file.

    Returns:
        bool: True if the installation is successful, False otherwise.
    """

    r = subprocess.run(['pip3', 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed: {}".format(path), file=sys.stderr)
        return False

    return True


def upload_file(upload):
    """Uploads a file using curl command.

    This function uploads a file to a specified location using the curl
    command.

    Args:
        upload (str): The URL where the file will be uploaded.

    Returns:
        bool: True if the file was uploaded successfully, False otherwise.
    """

    r1 = subprocess.run(['curl', '-XPUT', '-d', '@/tmp/output.tar.bz2', upload])
    print()
    if r1.returncode != 0:
        print("[COUT] upload error", file=sys.stderr)
        return False
    return True


def pynsist(file_name):
    """Run pynsist to create an installer using the specified configuration
    file.

    Args:
        file_name (str): The name of the configuration file.

    Returns:
        bool: True if the pynsist command ran successfully, False otherwise.
    """

    r = subprocess.run(['pynsist', '{}/{}'.format(REPO_PATH, file_name)])

    if r.returncode != 0:
        print("[COUT] pynsist error", file=sys.stderr)
        return False

    return True


def compress(file_name):
    """Compress a directory into a tar.bz2 file.

    This function compresses the contents of a specified directory into a
    tar.bz2 file.

    Args:
        file_name (str): The path to the directory to be compressed.

    Returns:
        bool: True if the compression is successful, False otherwise.
    """

    dirname = os.path.dirname(file_name)
    r = safe_command.run(subprocess.run, 'cd {}/{}/build/nsis; tar cjvf /tmp/output.tar.bz2 .'.format(REPO_PATH, dirname), shell=False)

    if r.returncode != 0:
        print("[COUT] compress error", file=sys.stderr)
        return False

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    It retrieves the 'CO_DATA' environment variable and parses it to extract
    key-value pairs. The function validates each pair based on a predefined
    list of valid keys. If a key is not recognized, a message is printed to
    notify about the unknown parameter.

    Returns:
        dict: A dictionary containing the extracted key-value pairs from 'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-file', 'upload']
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

    This function takes input arguments, checks for their presence, performs
    various tasks based on the arguments, and prints the result of the
    operation.
    """

    argv = parse_argument()
    git_url = argv.get('git-url')
    if not git_url:
        print("[COUT] The git-url value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

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

    if not pynsist(entry_file):
        print("[COUT] CO_RESULT = false")
        return

    if not compress(entry_file):
        print("[COUT] CO_RESULT = false")
        return

    if not upload_file(upload):
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
