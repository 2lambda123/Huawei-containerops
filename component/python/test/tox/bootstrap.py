#!/usr/bin/env python3

import subprocess
import os
import sys
import json
import anymarkup
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a git repository from the provided URL.

    This function clones a git repository from the specified URL to the
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
    """Setup a Python package from the specified path.

    This function sets up a Python package by running the installation
    command for the package.

    Args:
        path (str): The path to the Python package.

    Returns:
        bool: True if the setup was successful, False otherwise.
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
    """Install Python packages listed in the requirements file.

    This function uses pip to install packages listed in the specified
    requirements file.

    Args:
        file_name (str): The path to the requirements file.

    Returns:
        bool: True if the installation was successful, False otherwise.
    """

    r = subprocess.run(['pip3', 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed: {}".format(file_name), file=sys.stderr)
        return False

    return True


def tox(file_name):
    """Run tox for a specific file.

    This function runs tox for a specified file within a repository path. It
    executes the tox command and checks the return code to determine if the
    execution was successful.

    Args:
        file_name (str): The name of the file to run tox for.

    Returns:
        bool: True if tox execution was successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, 'cd {}/{}; tox --result-json /tmp/output.json'.format(REPO_PATH, file_name), shell=False)

    if r.returncode != 0:
        return False

    return True


def echo_json(use_yaml):
    """Print the content of a JSON file in either JSON or YAML format.

    This function loads the content of a JSON file located at
    '/tmp/output.json'. If 'use_yaml' is True, it serializes the data to
    YAML format and prints it. If 'use_yaml' is False, it prints the JSON
    data as it is.

    Args:
        use_yaml (bool): A flag to determine whether to output the data in YAML format.

    Returns:
        bool: True if the function executes successfully.
    """

    data = json.load(open('/tmp/output.json'))
    if use_yaml:
        data = anymarkup.serialize(data, 'yaml')
        print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
    else:
        print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(data)))

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' to extract key-value pairs and
    return them as a dictionary.

    If 'CO_DATA' is not set or empty, an empty dictionary is returned.

    Returns:
        dict: A dictionary containing key-value pairs extracted from 'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-path', 'out-put-type']
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
    """Main function to perform a series of tasks including cloning a git
    repository,
    running tox, and printing the result.
    """

    argv = parse_argument()
    git_url = argv.get('git-url')
    if not git_url:
        print("[COUT] The git-url value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    entry_path = argv.get('entry-path')
    if not entry_path:
        print("[COUT] The entry-path value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    if not git_clone(git_url):
        return

    out = tox(entry_path)

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    echo_json(use_yaml)

    if not out:
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
