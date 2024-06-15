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
    """Returns the appropriate pip command based on the Python version
    provided.

    Args:
        version (str): The Python version for which the pip command is needed.

    Returns:
        str: The pip command to be used based on the provided Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def init_env(version):
    """Initialize the environment by installing pylama using the specified
    version of pip.

    Args:
        version (str): The version of pip to be used for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pylama'])


def validate_version(version):
    """Validate the input version against a list of valid versions.

    It checks if the input version is in the list of valid versions.

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


def pylama(file_name, use_yaml):
    """Run pylama on a specified file and return the results.

    Args:
        file_name (str): The name of the file to run pylama on.
        use_yaml (bool): A flag indicating whether to output results in YAML format.

    Returns:
        bool: True if pylama ran successfully without any issues, False otherwise.
    """

    r = subprocess.run(['pylama', file_name], stderr=subprocess.PIPE,
                       stdout=subprocess.PIPE)

    passed = True
    if (r.returncode != 0):
        passed = False

    out = str(r.stdout, 'utf-8').strip().split('\n')
    retval = []
    for o in out:
        o = parse_pylama_result(o)
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


def parse_pylama_result(line):
    """Parse a line of Pylama result and extract relevant information.

    This function takes a line of Pylama result, splits it by colon, and
    extracts file path, line number, column number, and the message. It then
    returns a dictionary containing these extracted values.

    Args:
        line (str): A line of Pylama result to be parsed.

    Returns:
        dict or bool: A dictionary containing file path, line number, column
            number, and message if the line is valid,
            otherwise False.
    """

    line = line.split(':')
    if (len(line) < 4):
        return False
    return {'file': trim_repo_path(line[0]), 'line': line[1], 'col': line[2], 'msg': line[3]}

def trim_repo_path(n):
    """Trims the repository path from a given string.

    This function takes a string as input and trims the repository path from
    it by removing the characters up to and including the repository path.
    The repository path is defined by the constant REPO_PATH.

    Args:
        n (str): The input string from which the repository path needs to be trimmed.

    Returns:
        str: The trimmed string without the repository path.
    """

    return n[len(REPO_PATH) + 1:]


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    It retrieves the 'CO_DATA' environment variable and parses it to extract
    key-value pairs based on specific validation criteria. If the 'CO_DATA'
    is not set or empty, an empty dictionary is returned. The 'CO_DATA'
    string is split by space, and each key-value pair is extracted by
    splitting at '='. Key-value pairs are validated against a predefined
    list of keys.

    Returns:
        dict: A dictionary containing the extracted key-value pairs from 'CO_DATA'.
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
    """Main function to perform a series of tasks based on the input arguments.

    It parses the command line arguments, validates the input, initializes
    the environment, clones a git repository, runs a static code analysis
    tool on Python files in the repository, and prints the result.
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
                o = pylama(os.path.join(root, file_name), use_yaml)
                all_true = all_true and o

    if all_true:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")

main()
