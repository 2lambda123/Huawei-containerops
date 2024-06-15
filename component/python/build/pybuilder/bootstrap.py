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
    r = subprocess.run(['git', 'clone', url, REPO_PATH])

    if r.returncode == 0:
        return True
    else:
        print("[COUT] Git clone error: Invalid argument to exit",
              file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return False


def get_pip_cmd(version):
    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def get_python_cmd(version):
    if version == 'py3k' or version == 'python3':
        return 'python3'

    return 'python'


def init_env(version):
    safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', 'pybuilder', 'six'])


def validate_version(version):
    valid_version = ['python', 'python2', 'python3', 'py3k']
    if version not in valid_version:
        print("[COUT] Check version failed: the valid version is {}".format(valid_version), file=sys.stderr)
        return False

    return True


def setup(path, version='py3k'):
    file_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    r = safe_command.run(subprocess.run, 'cd {}; {} {} install'.format(dir_name, get_python_cmd(version), file_name),
                       shell=False)

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def pip_install(file_name, version='py3k'):
    r = safe_command.run(subprocess.run, [get_pip_cmd(version), 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def pybuilder(dir_name, task):
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
