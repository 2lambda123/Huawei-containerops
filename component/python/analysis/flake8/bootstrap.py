#!/usr/bin/env python3

import subprocess
import os
import sys
import json
import yaml
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a Git repository from the provided URL.

    This function clones a Git repository from the specified URL to the
    predefined REPO_PATH.

    Args:
        url (str): The URL of the Git repository to clone.

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
            Should be either 'py3k' or 'python3'.

    Returns:
        str: The appropriate pip command based on the provided Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def init_env(version):
    """Initialize the environment by installing flake8 using the specified
    version of pip.

    Args:
        version (str): The version of pip to use for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'flake8'])


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


def flake8(file_name, use_yaml):
    """Run flake8 on a specified file and return the results.

    Args:
        file_name (str): The name of the file to run flake8 on.
        use_yaml (bool): A flag indicating whether to output results in YAML format.

    Returns:
        bool: True if flake8 passed without any issues, False otherwise.
    """

    r = subprocess.run(['flake8', file_name], stderr=subprocess.PIPE,
                       stdout=subprocess.PIPE)

    passed = True
    if (r.returncode != 0):
        passed = False

    out = str(r.stdout, 'utf-8').strip().split('\n')
    retval = []
    for o in out:
        o = parse_flake8_result(o)
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


def parse_flake8_result(line):
    """Parse a line from Flake8 result output to extract file path, line
    number, column number, and message.

    Args:
        line (str): A string representing a line from Flake8 result output.

    Returns:
        dict: A dictionary containing the extracted information.
            - 'file' (str): The file path.
            - 'line' (str): The line number.
            - 'col' (str): The column number.
            - 'msg' (str): The message.
    """

    line = line.split(':')
    if (len(line) < 4):
        return False
    return {'file': trim_repo_path(line[0]), 'line': line[1], 'col': line[2], 'msg': line[3]}

def trim_repo_path(n):
    """Trims the repository path from the input string.

    This function takes an input string and removes the repository path from
    it, returning only the path relative to the repository.

    Args:
        n (str): The input string containing the full path.

    Returns:
        str: The trimmed path relative to the repository.
    """

    return n[len(REPO_PATH) + 1:]


def parse_argument():
    """Parse the environment variable 'CO_DATA' to extract key-value pairs and
    return them as a dictionary.

    If the 'CO_DATA' environment variable is not set or empty, an empty
    dictionary is returned.

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
    """Main function to perform a series of tasks including validating
    arguments, cloning a git repository,
    running flake8 on Python files, and printing the result.
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
                o = flake8(os.path.join(root, file_name), use_yaml)
                all_true = all_true and o

    if all_true:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")

main()
