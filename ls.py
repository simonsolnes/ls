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

def strip_ansi(string):
    return bash("sed -r \"s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g\" <<<\"" + string + '"')

gitformat = {
	'?': ['normal', 'red'],
	'M': ['normal', 'red'],
	'U': ['normal', 'red'],
	'A': ['normal', 'green'],
	'D': ['normal', 'green'],
	'R': ['normal', 'green'],
	'C': ['normal', 'green'],
	' ': []
}

typeformat = {
	'file':			[],
	'exec':			['italic', 'green'],
	'symlink':		['italic', 'yellow'],
	'dotfile':		['faint'],
	'dir':			['bold', 'magenta'],
}


class Git():
	def __init__(self, path):
		self.git = False
		if path == './':
			try:
				subprocess.check_output('git rev-parse --is-inside-work-tree 2>&1 >/dev/null',shell=True)
				self.stats = {f[3:]: f[:2] for f in strip_ansi(bash('git status --short')).split('\n') if f}
				self.git = True
			except:
				self.git = False

	def get_status(self, path):
		if self.git == False:
			return ''
		status = self.stats.get(path, '  ')
		if len(status) != 2:
			return '  '
		X, Y = status
		X = colorize(X, *gitformat.get(X, []))
		Y = colorize(Y, *gitformat.get(Y, []))
		return X + Y + ' '
		
	
class File(threading.Thread):
	def __init__(self, root, name, git):
		threading.Thread.__init__(self)
		self.root = root
		self.name = name
		self.path = root + name
		self.git = git.get_status(self.name)

	def run(self):
		stat = os.lstat(self.path)
		mode = int(oct(stat[0])[2:-3])
		self.size = stat[6]
		self.filetype = 'file'
		self.children = 0

		try:
			if (int(oct(stat[0])[-3:][0]) + 1) % 2 == 0 and mode == 100:
				self.filetype = 'exec'
			if mode == 40:
				self.filetype = 'dir'
				self.name += '/'
				self.children = len(os.listdir(self.path))
			if self.name[0] == '.' and len(self.name) > 1 and self.name[1] != '.':
				self.filetype = 'dotfile'
			if mode == 120:
				if self.filetype == 'file':
					self.filetype = 'symlink' 
				self.realpath = os.path.relpath(os.path.realpath(self.path))
		except:
			pass

	def __repr__(self):
		git = self.git
		size = colorize(human_size(self.size).rjust(6), 'faint') + ' '
		name = colorize(self.name, *typeformat[self.filetype]) + ' '
		children = ''
		points = ''
		if self.filetype == 'dir':
			children = colorize('[' + str(self.children) + ']', 'faint')
		if self.filetype == 'symlink':
			points = colorize('→ ' + self.realpath, 'faint')
		
		return git + size + name + children + points
		
def main():
	if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
		root = sys.argv[1] + '/'
	else:
		root = './'
	git = Git(root)
	files = []
	for f in os.listdir(root):
		files.append(File(root, f, git))
	for f in files:
		f.start()
	for f in files:
		f.join()
	files = sorted(files, key=lambda x: x.name.lower())
	for f in files:
		print(f)
	
if __name__ == '__main__':
	main()
