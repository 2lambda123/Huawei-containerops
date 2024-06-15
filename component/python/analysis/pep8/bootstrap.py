#!/usr/bin/env python3

import subprocess
import os
import sys
import json
import yaml
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

    if (r.returncode == 0):
        return True
    else:
        print("[COUT] Git clone error: Invalid argument to exit", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return False


def get_pip_cmd(version):
    """Return the appropriate pip command based on the Python version provided.

    This function takes a Python version as input and returns the
    corresponding pip command.

    Args:
        version (str): The Python version for which the pip command is needed.

    Returns:
        str: The pip command based on the input Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def init_env(version):
    """Initialize the environment by installing the 'pep8' package using pip
    for the specified Python version.

    Args:
        version (str): The Python version for which the 'pep8' package needs to be installed.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pep8'])


def validate_version(version):
    """Validate the input version against a list of valid versions.

    It checks if the input version is present in the list of valid versions.

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


def pep8(file_name, use_yaml):
    """Check PEP8 compliance of a Python file using the PEP8 tool.

    This function runs the PEP8 tool on a specified Python file and checks
    if it complies with the PEP8 style guide. It returns True if the file
    passes the PEP8 checks, otherwise returns False.

    Args:
        file_name (str): The name of the Python file to be checked.
        use_yaml (bool): Flag indicating whether to output the results in YAML format.

    Returns:
        bool: True if the file passes PEP8 checks, False otherwise.
    """

    r = subprocess.run(['pep8', file_name], stderr=subprocess.PIPE,
                       stdout=subprocess.PIPE)

    passed = True
    if (r.returncode != 0):
        passed = False

    out = str(r.stdout, 'utf-8').strip().split('\n')
    retval = []
    for o in out:
        o = parse_pep8_result(o)
        if o:
            retval.append(o)

    if len(retval) > 0:
        out = {"results": { "cli": retval }}
        if use_yaml:
            out = bytes(yaml.safe_dump(out), 'utf-8')
            print('[COUT] CO_YAML_CONTENT {}'.format(str(out)[1:]))
        else:
            print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(out)))

    return passed


def parse_pep8_result(line):
    """Parse the PEP8 result line and extract relevant information.

    This function takes a PEP8 result line as input, splits it by colon, and
    extracts the file path, line number, column number, and message from the
    line.

    Args:
        line (str): A string representing a single PEP8 result line.

    Returns:
        dict: A dictionary containing the extracted information.
            - 'file' (str): The file path where the PEP8 result occurred.
            - 'line' (str): The line number where the PEP8 result occurred.
            - 'col' (str): The column number where the PEP8 result occurred.
            - 'msg' (str): The message describing the PEP8 result.
    """

    line = line.split(':')
    if (len(line) < 4):
        return False
    return {'file': trim_repo_path(line[0]), 'line': line[1], 'col': line[2], 'msg': line[3]}

def trim_repo_path(n):
    """Trims the repository path from a given string.

    This function takes a string and removes the repository path prefix from
    it.

    Args:
        n (str): The input string with the repository path.

    Returns:
        str: The input string with the repository path prefix removed.
    """

    return n[len(REPO_PATH) + 1:]


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific criteria.

    It retrieves the 'CO_DATA' environment variable and parses it to extract
    key-value pairs. The function validates the keys against a predefined
    list and constructs a dictionary of valid key-value pairs.

    Returns:
        dict: A dictionary containing key-value pairs extracted from the 'CO_DATA'
            environment variable.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'version', 'out-put-type']
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
    """Main function to perform code analysis on a git repository.

    This function parses command line arguments, validates the version,
    initializes the environment, clones the git repository, and performs
    PEP8 style checks on Python files in the repository.
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

    if not git_clone(git_url):
        return

    all_true = True
    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    for root, dirs, files in os.walk(REPO_PATH):
        for file_name in files:
            if file_name.endswith('.py'):
                o = pep8(os.path.join(root, file_name), use_yaml)
                all_true = all_true and o

    if all_true:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
