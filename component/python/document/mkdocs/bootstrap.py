#!/usr/bin/env python3

import subprocess
import os
import sys
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


def mkdocs(dir_name):
    r = safe_command.run(subprocess.run, 'cd {}/{}; mkdocs json'.format(REPO_PATH, dir_name), shell=False)

    if r.returncode != 0:
        print("[COUT] mkdocs error", file=sys.stderr)
        return False

    return True


def echo_json(dir_name, use_yaml):
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
