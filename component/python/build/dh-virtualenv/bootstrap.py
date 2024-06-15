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


def upload_file(upload):
    """Uploads a Debian package file to a specified location using curl.

    This function uploads a Debian package file to the specified 'upload'
    location using curl command.

    Args:
        upload (str): The URL where the file will be uploaded.

    Returns:
        bool: True if the file was uploaded successfully, False otherwise.
    """

    file_name = glob.glob('*.deb')[0]
    r1 = subprocess.run(['curl', '-XPUT', '-d', '@' + file_name, upload])
    if r1.returncode != 0:
        print("[COUT] upload error", file=sys.stderr)
        return False
    print()
    return True


def build():
    """Build the project using mk-build-deps and dpkg-buildpackage commands.

    It runs mk-build-deps to install build dependencies and then runs dpkg-
    buildpackage to build the project.

    Returns:
        bool: True if the build is successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, 'cd {}; yes | mk-build-deps -ri; dpkg-buildpackage -us -uc -b'.format(REPO_PATH), shell=False)

    if r.returncode != 0:
        print("[COUT] build error", file=sys.stderr)
        return False

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs.

    It retrieves the 'CO_DATA' environment variable and parses it to extract
    key-value pairs. The function validates the keys against a predefined
    list and returns a dictionary of valid key-value pairs.

    Returns:
        dict: A dictionary containing valid key-value pairs extracted from 'CO_DATA'.
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
    """Main function to perform a series of actions including git cloning,
    building, and uploading files.

    This function takes command line arguments, extracts the git URL and
    upload path from the arguments, performs git cloning, builds the
    project, uploads the files, and prints the CO_RESULT based on success.
    """

    argv = parse_argument()
    git_url = argv.get('git-url')
    if not git_url:
        print("[COUT] The git-url value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    upload = argv.get('upload')
    if not upload:
        print("[COUT] The upload value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    if not git_clone(git_url):
        return

    if not build():
        print("[COUT] CO_RESULT = false")
        return

    if not upload_file(upload):
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
