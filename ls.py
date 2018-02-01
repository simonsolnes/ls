#!/usr/bin/env python3
import os
import subprocess
import sys
import threading
import queue

bash = lambda cmd: subprocess.check_output(cmd, shell=True).decode('utf-8')

def colorize(x, frmt='normal', fg='normal', bg='normal'):
    c = {"black" : 0, "red" : 1, "green" : 2, "yellow" : 3, "blue" : 4, "magenta" : 5, "cyan" : 6, "white" : 7, "normal" : 8}
    f = {"normal" : 0, "bold" : 1, "faint" : 2, "italic" : 3, "underline" : 4}
    return '\x1b['+str(f[frmt])+';'+str(30+c[fg])+';'+str(40+c[bg])+'m'+x+'\x1b[0m'

def human_size(number):
	nums = [(number / (1024.0 ** i), unit) for i, unit in enumerate(' KMGTPEZY')]
	filtered = [num for i, num in enumerate(nums) if num[0] < 1024 or i == len(nums) - 1]
	return str(round(filtered[0][0])).rjust(3) + str(' ' + (filtered[0][1] + 'iB' if filtered[0][1] != ' ' else 'B')).ljust(4)

sizeformat = lambda x: colorize(human_size(x).rjust(6), 'faint')

childrenformat = lambda x: colorize('[' + str(x) + ' ☰ ]', 'faint')

realfileformat = lambda x: colorize('→ ', 'bold') + (typeformat[x['type']](x['name']) if isinstance(x, dict) else colorize('broken link', fg='red'))

gitformat = {
    '?': lambda x: colorize(x, fg='red'),
    'M': lambda x: colorize(x, fg='red'),
    'U': lambda x: colorize(x, fg='red'),
    'A': lambda x: colorize(x, fg='green'),
    'D': lambda x: colorize(x, fg='green'),
    'R': lambda x: colorize(x, fg='green'),
    'C': lambda x: colorize(x, fg='green'),
    ' ': lambda x: ' '
}

typeformat = {
    'file':			lambda x: colorize(x),
    'exec':			lambda x: colorize(x, 'italic', 'green'),
    'symlink':		lambda x: colorize(x, 'italic', 'yellow'),
    'dotfile':		lambda x: colorize(x, 'faint'),
    'directory':	lambda x: colorize(x, 'bold', 'magenta'),
}

def get_data(stat, path, name):
    mode = int(oct(stat[0])[2:-3])
    size =  stat[6]
    metadata = {}
    filetype = 'file'

    if (int(oct(stat[0])[-3:][0]) + 1) % 2 == 0 and mode == 100:
        filetype = 'exec'
    if mode == 40:
        filetype = 'directory'
        name += '/'
        metadata['children'] = len(os.listdir(path))
    if name[0] == '.' and len(name) > 1 and name[1] != '.':
        filetype = 'dotfile'
    if mode == 120:
        if filetype == 'file':
            filetype = 'symlink' 
        realpath = os.path.relpath(os.path.realpath(path))
        if os.path.isfile(realpath) or os.path.isdir(realpath):
            metadata['realfile'] = get_data(os.lstat(realpath), realpath, realpath) 
            size = metadata['realfile']['size']
            del metadata['realfile']['size']
        else:
            metadata['realfile'] = 'broken link'
    return {'name': name, 'path': path, 'type': filetype, 'size': size, 'metadata': metadata}


if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    path = sys.argv[1]
    git = False
else:
    path = './'
    try:
        bash('git rev-parse --is-inside-work-tree 2>&1 >/dev/null')
        git = {f[3:].split('/')[-1]: f[:2] for f in bash('git status --short').split('\n')}
    except:
        git = False

for f in sorted(os.listdir(path), key=lambda x: x.lower()):
    try:
        data = get_data(os.lstat(path + f), path + f, f) 
    except:
        data = {'name': f, 'type': 'file', 'size': 0, 'metadata': {}}
    if git:
        X, Y = git.get(data['name'], '  ')
        print(gitformat[X](X) + gitformat[Y](Y), end=' ')
    print(sizeformat(data['size']), end=' ')
    print(typeformat[data['type']](data['name']), end=' ')
    if 'realfile' in data['metadata']:
        print(realfileformat(data['metadata']['realfile']), end='')
    if 'children' in data['metadata']:
        print(childrenformat(data['metadata']['children']), end='')
    print(end=' ')
    print()
