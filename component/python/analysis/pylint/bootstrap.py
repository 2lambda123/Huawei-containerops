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

    This function clones a git repository from the specified URL to the
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
    """Determine the appropriate pip command based on the Python version
    provided.

    Args:
        version (str): The Python version for which to determine the pip command.

    Returns:
        str: The appropriate pip command based on the provided Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def init_env(version):
    """Initialize the environment by installing pylint for the specified Python
    version.

    Args:
        version (str): The Python version for which pylint needs to be installed.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pylint'])


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


def pylint(file_name, rcfile, use_yaml):
    """Run pylint on a specified file and return the results.

    This function runs pylint on the given file using the specified rcfile
    if provided, otherwise it uses the default rcfile. It then processes the
    output and returns the results.

    Args:
        file_name (str): The name of the file to run pylint on.
        rcfile (str): The name of the rcfile to use for pylint configuration.
        use_yaml (bool): A flag indicating whether to output results in YAML format.

    Returns:
        bool: True if pylint ran successfully, False otherwise.
    """

    if rcfile:
        rcfile = '--rcfile={}/{}'.format(REPO_PATH, rcfile)
    else:
        rcfile = '--rcfile=/root/.pylintrc'
    r = subprocess.run(['pylint', '-f', 'json', rcfile, file_name], stdout=subprocess.PIPE)

    passed = True
    if (r.returncode != 0):
        passed = False

    out = str(r.stdout, 'utf-8').strip()
    retval = []
    for o in json.loads(out):
        o['path'] = trim_repo_path(o['path'])
        retval.append(o)

    if len(retval) > 0:
        out = {"results": { "cli": retval }}
        if use_yaml:
            out = bytes(yaml.safe_dump(out), 'utf-8')
            print('[COUT] CO_YAML_CONTENT {}'.format(str(out)[1:]))
        else:
            print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(out)))

    return passed


def trim_repo_path(n):
    """Trims the repository path from the given string.

    This function takes a string and removes the repository path prefix from
    it.

    Args:
        n (str): The input string containing the full path.

    Returns:
        str: The trimmed string without the repository path.
    """

    return n[len(REPO_PATH) + 1:]


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    If the 'CO_DATA' environment variable is not set or empty, an empty
    dictionary is returned. The 'CO_DATA' string is split by space and each
    key-value pair is extracted based on the format 'key=value'. Only key-
    value pairs with keys in the validation list ['git-url', 'rcfile',
    'version', 'out-put-type'] are considered.

    Returns:
        dict: A dictionary containing key-value pairs extracted from the 'CO_DATA'
            environment variable.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'rcfile', 'version', 'out-put-type']
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
    initializes the environment, clones the git repository, runs pylint on
    Python files in the repository, and prints the analysis result.
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

    rcfile = argv.get('rcfile')

    if not git_clone(git_url):
        return

    all_true = True
    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    for root, dirs, files in os.walk(REPO_PATH):
        for file_name in files:
            if file_name.endswith('.py'):
                o = pylint(os.path.join(root, file_name), rcfile, use_yaml)
                all_true = all_true and o

    if all_true:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
