#!/usr/bin/env python3

import subprocess
import os
import sys
import glob
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


def get_pip_cmd(version):
    """Determine the appropriate pip command based on the Python version
    provided.

    Args:
        version (str): The Python version for which to determine the pip command.

    Returns:
        str: The appropriate pip command based on the Python version.
    """

    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def get_python_cmd(version):
    """Return the appropriate Python command based on the given version.

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
    """Initialize the environment by installing 'pybuilder' and 'six' using the
    specified version of pip command.

    Args:
        version (str): The version of pip command to be used for installation.
    """

    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pybuilder', 'six'])


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
    """Setup the specified Python package located at the given path.

    This function installs the Python package located at the specified path
    by running the installation command in the directory containing the
    package file. It uses the provided Python version or defaults to 'py3k'.

    Args:
        path (str): The path to the Python package file.
        version (str?): The Python version to use for installation. Defaults to 'py3k'.

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


def pybuilder(dir_name, task):
    """Run PyBuilder task in a specified directory.

    This function runs a PyBuilder task in the specified directory. If no
    directory is provided, it runs the task in the main repository path.

    Args:
        dir_name (str): The directory path where the PyBuilder task will be executed.
        task (str): The PyBuilder task to be executed.

    Returns:
        bool: True if the PyBuilder task was executed successfully, False otherwise.
    """

    if dir_name and dir_name != '.':
        dir_name = '{}/{}'.format(REPO_PATH, dir_name)
    else:
        dir_name = REPO_PATH

    r = safe_command.run(subprocess.run, 'cd {}; pyb {}'.format(dir_name, task), shell=False)

    if r.returncode != 0:
        print("[COUT] pybuilder error", file=sys.stderr)
        return False

    return True


def echo_json(dir_name, use_yaml):
    """Print the content of JSON files in the specified directory.

    This function iterates through all JSON files in the target directory
    and prints their content. If 'use_yaml' is True, the content is also
    serialized to YAML format before printing.

    Args:
        dir_name (str): The directory path where JSON files are located.
        use_yaml (bool): A flag indicating whether to print content in YAML format.

    Returns:
        bool: True if the function executes successfully.
    """

    if dir_name and dir_name != '.':
        dir_name = '{}/{}'.format(REPO_PATH, dir_name)
    else:
        dir_name = REPO_PATH
    for root, dirs, files in os.walk('{}/target'.format(dir_name)):
        for file_name in files:
            if file_name.endswith('.json'):
                data = json.load(open(os.path.join(root, file_name)))
                if use_yaml:
                    data = anymarkup.serialize(data, 'yaml')
                    print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
                else:
                    print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps(data)))

    return True

def echo_xml(dir_name, use_yaml):
    """Echo XML content from files in the specified directory.

    This function reads XML files from the target directory and prints their
    contents. If use_yaml is True, it converts the XML content to YAML
    before printing.

    Args:
        dir_name (str): The directory path where XML files are located.
        use_yaml (bool): Flag to indicate whether to convert XML to YAML.

    Returns:
        bool: True if the function executes successfully.
    """

    if dir_name and dir_name != '.':
        dir_name = '{}/{}'.format(REPO_PATH, dir_name)
    else:
        dir_name = REPO_PATH
    for root, dirs, files in os.walk('{}/target'.format(dir_name)):
        for file_name in files:
            if file_name.endswith('.xml'):
                if use_yaml:
                    data = anymarkup.parse_file(os.path.join(root, file_name))
                    data = anymarkup.serialize(data, 'yaml')
                    print('[COUT] CO_YAML_CONTENT {}'.format(str(data)[1:]))
                    continue
                with open(os.path.join(root, file_name), 'rb') as f:
                    data = f.read()
                    print('[COUT] CO_XML_CONTENT {}'.format(str(data)[1:]))

    return True


def parse_argument():
    """Parse the environment variable 'CO_DATA' and extract key-value pairs.

    It parses the environment variable 'CO_DATA' to extract key-value pairs
    separated by '='. If the 'CO_DATA' is not set or empty, it returns an
    empty dictionary.

    Returns:
        dict: A dictionary containing key-value pairs extracted from 'CO_DATA'.
    """

    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-path', 'task', 'version', 'out-put-type']
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

    This function parses command line arguments, validates the version,
    initializes the environment, clones a git repository, sets up Python
    projects, installs dependencies, runs PyBuilder tasks, and outputs
    results in JSON or YAML format.
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

    entry_path = argv.get('entry-path', '.')
    task = argv.get('task')

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

    out = pybuilder(entry_path, task)
    use_yaml = argv.get('out-put-type', 'json') == 'yaml'

    echo_json(entry_path, use_yaml)
    echo_xml(entry_path, use_yaml)

    if not out:
        print("[COUT] CO_RESULT = false")
    else:
        print("[COUT] CO_RESULT = true")


main()
