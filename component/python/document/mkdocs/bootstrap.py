#!/usr/bin/env python3

import subprocess
import os
import sys
import json
import anymarkup
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a git repository from the given URL.

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


def mkdocs(dir_name):
    """Generate mkdocs JSON for a specific directory.

    This function runs the 'mkdocs json' command for the specified directory
    within the repository path.

    Args:
        dir_name (str): The name of the directory for which mkdocs JSON needs to be generated.

    Returns:
        bool: True if mkdocs JSON generation is successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, 'cd {}/{}; mkdocs json'.format(REPO_PATH, dir_name), shell=False)

    if r.returncode != 0:
        print("[COUT] mkdocs error", file=sys.stderr)
        return False

    return True


def echo_json(dir_name, use_yaml):
    """Echo the content of JSON files in the specified directory.

    This function walks through the directory specified by 'dir_name' and
    prints the content of each JSON file found. If 'use_yaml' is True, the
    JSON content is converted to YAML before printing.

    Args:
        dir_name (str): The name of the directory to search for JSON files.
        use_yaml (bool): A flag indicating whether to convert JSON to YAML before printing.

    Returns:
        bool: True if the function executes successfully.
    """

    for root, dirs, files in os.walk('{}/{}'.format(REPO_PATH, dir_name)):
        for file_name in files:
            if file_name.endswith('.json'):
                data = json.load(open(os.path.join(root, file_name)))
                if use_yaml:
                    data = anymarkup.serialize(data, 'yaml')
                    print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
                else:
                    print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(data)))

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    If the 'CO_DATA' environment variable is not set or empty, an empty
    dictionary is returned. The function iterates through the space-
    separated key-value pairs in 'CO_DATA', validates each pair, and
    constructs a dictionary with valid key-value pairs.

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
    """Main function to perform a series of tasks based on input arguments.

    It parses the command line arguments, retrieves the git URL and entry
    path from the arguments. If either git URL or entry path is missing, it
    prints an error message and returns. It then clones the git repository
    using the provided URL. If cloning fails, it returns. It generates
    mkdocs based on the provided entry path. If mkdocs generation fails, it
    prints an error message and returns. It determines the output type based
    on the input arguments. If the output type is YAML, it echoes the JSON
    content in YAML format. If echoing fails, it prints an error message and
    returns. Finally, it prints CO_RESULT = true if all tasks are
    successful.
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

    if not mkdocs(entry_path):
        print("[COUT] CO_RESULT = false")
        return

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    if not echo_json(entry_path, use_yaml):
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
