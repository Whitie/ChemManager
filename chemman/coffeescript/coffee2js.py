#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import subprocess


IN_PATTERN = '*.coffee'
OUTFILE = '../core/static/core/js/cm.js'
TIMEOUT_SEC = 20


def safe_write(filepath, content):
    _path = os.path.abspath(filepath)
    path = '{}~'.format(_path)
    with open(path, 'w', encoding='utf-8') as fp:
        fp.write(content)
    if os.path.isfile(_path):
        os.remove(_path)
    os.rename(path, _path)


def main():
    path = os.path.abspath(os.getcwd())
    file_contents = []
    for filename in glob.glob(os.path.join(path, IN_PATTERN)):
        with open(filename, encoding='utf-8') as fp:
            file_contents.append(fp.read())
    coffee = subprocess.Popen(
        ['coffee', '-c', '-s', '-b'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    try:
        out, _ = coffee.communicate(input='\n\n'.join(file_contents),
                                    timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        coffee.kill()
        raise
    safe_write(OUTFILE, out)


if __name__ == '__main__':
    main()
