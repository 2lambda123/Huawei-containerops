#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
from bs4 import BeautifulSoup
import json
import anymarkup
from security import safe_command

REPO_PATH = 'git-repo'


def git_clone(url):
    """Clone a git repository from the provided URL.

    This function clones a git repository from the given URL to the
    predefined repository path.

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
        version (str): The Python version for which to determine the pip command.

    Returns:
        str: The pip command to be used based on the provided Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def get_python_cmd(version):
    """Returns the appropriate Python command based on the input version.

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
    """Initialize the environment by installing 'pdoc' package using pip for
    the specified version.

    Args:
        version (str): The version of Python for which 'pdoc' package needs to be installed.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pdoc'])


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


def setup(path, version='py3k'):
    """Set up the Python environment by installing dependencies from a given
    path.

    Args:
        path (str): The path to the directory containing the dependencies.
        version (str): The Python version to use for installation (default is 'py3k').

    Returns:
        bool: True if the setup was successful, False otherwise.
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


def pdoc(mod):
    """Generate HTML documentation using pdoc for the specified module.

    This function runs the pdoc command to generate HTML documentation for
    the specified module.

    Args:
        mod (str): The name of the module for which documentation needs to be generated.

    Returns:
        bool: True if the documentation generation is successful, False otherwise.
    """

    r = safe_command.run(subprocess.run, 'pdoc --html-dir /tmp/output --html {} --all-submodules'.format(mod), shell=False)

    if r.returncode != 0:
        print("[COUT] pdoc error", file=sys.stderr)
        return False

    return True


def echo_json(use_yaml):
    """Echo the content of HTML files in a directory as JSON or YAML format.

    This function walks through the '/tmp/output' directory, reads each HTML
    file, extracts the title and body content, and converts it into a JSON
    or YAML format.

    Args:
        use_yaml (bool): A boolean flag to determine whether to output in YAML format.

    Returns:
        bool: True if the function executes successfully.
    """

    for root, dirs, files in os.walk('/tmp/output'):
        for file_name in files:
            if file_name.endswith('.html'):
                with open(os.path.join(root, file_name), 'r') as f:
                    data = f.read()
                    soup = BeautifulSoup(data, 'html.parser')
                    title = soup.find('title').text
                    body = soup.find('body').renderContents()
                    data = {
                        "title": title,
                        "body": str(body, 'utf-8', errors='ignore'),
                        "file": file_name
                    }
                    if use_yaml:
                        data = anymarkup.serialize(data, 'yaml')
                        print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
                    else:
                        print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(data)))


    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs
    based on specific validation criteria.

    It retrieves the 'CO_DATA' environment variable and parses it to extract
    key-value pairs. The function validates the extracted pairs against a
    predefined list of keys. If a key is not recognized or a pair is
    incomplete, a message is printed and the pair is skipped.

    Returns:
        dict: A dictionary containing the valid key-value pairs extracted from
            'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-mod', 'version', 'out-put-type']
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
    """Main function to process input arguments, clone git repository, setup
    environment,
    install dependencies, generate documentation, and output results.
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

    entry_mod = argv.get('entry-mod')
    if not entry_mod:
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


    out = pdoc(entry_mod)

    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    echo_json(use_yaml)

    if out:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
