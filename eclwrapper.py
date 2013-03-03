#!/usr/bin/env python

import pexpect
import readline
import os
import sys
import tty
import termios
import string
import signal
import curses.ascii

class EclWrapper(object):

	def ignored(self, c):
		n = ord(c)
		if n in (curses.ascii.DC1, curses.ascii.DC2, curses.ascii.DC3, curses.ascii.DC4):
			return True
		elif n == curses.ascii.SUB:
			return True
		elif n == curses.ascii.SO:
			return True
		else:
			return False

	def unbuf(self):
		if self.__buffered:
			self.__fd = sys.stdin.fileno()
			self.__old_settings = termios.tcgetattr(self.__fd)
			tty.setraw(self.__fd)
			self.__buffered = False

	def buf(self):
		if not self.__buffered:
			termios.tcsetattr(self.__fd, termios.TCSADRAIN, self.__old_settings)
			self.__buffered = True

	def buffered(self):
		return self.__buffered

	def getch(self):
		if self.__buffered: self.unbuf()
		p = sys.stdin.read(1)
		if p == '':
			raise EOFError
		return p

	def getline(self, prompt):
		if not self.__buffered: self.buf()
		return raw_input(self.child.after)

	def __ignore_int(self):
		def handler(signum, frame):
			self.__int = True
		if signal.getsignal(signal.SIGINT) != handler:
			self.__int = False
			self.__oldhandler = signal.signal(signal.SIGINT, handler)

	def __default_int(self):
		try:
			signal.signal(signal.SIGINT, self.__oldhandler)
			del self.__oldhandler
		except AttributeError:
			pass
		else:
			if self.__int: raise KeyboardInterrupt
		finally:
			self.__int = False

	def __init__(self, eclpath, args):
		self.__buffered = True
		self.__interrupts = []
		self.__ignore_int()
		# Regular Expression for the case of remaining solutions
		self.moresols = r'((Yes \([^\)\(\n]+\))|((Type|interruption\:) [^\?\n]+)) \? $'
		# Regular Expression for command prompt pop-up
		self.prompt = r'\[eclipse [0-9]+\]\: $'
		# Regular Expression for unterminated command
		self.rest = r'((^\t)|(continue\r\n))$'
		# Newline Used by ECLiPSe
		self.linesep = '\r\n'
		# Call ECLiPSe Shell
		self.child = pexpect.spawn(eclpath, args)
		# Compile Pattern List
		self.cpl = self.child.compile_pattern_list([self.prompt, self.moresols, self.rest, pexpect.EOF])

	def __del__(self):
		self.buf()
		self.child.close(force = True)

	def __call__(self, *args):
		try:
			# Main Loop
			while True:
			#while self.child.isalive():#
				try:
					self.__default_int()
					s = self.child.expect_list(self.cpl)
					self.__ignore_int()
					sys.stdout.write(self.child.before)

					# Renew interruption flag and <s> variable (cont'd case)
					if s != 1 and self.__interrupts:
						bf = self.__interrupts.pop()
						if s == 2: s = 0 if bf else 1

					# More (?)
					if s == 1:
						self.unbuf()
						# Read Single Character
						sys.stdout.write(self.child.after)
						self.__default_int()
						ch = self.getch()
						self.__ignore_int()
						# Control Character
						if curses.ascii.iscntrl(ch):
							## print curses.ascii.unctrl(ch) ##
							# Substitute Unwanted Control Characters
							c = '[' if self.ignored(ch) else curses.ascii.unctrl(ch)[-1]
							# ^C Case
							if c.upper() == 'C':
								raise KeyboardInterrupt
							else:
								self.child.sendcontrol(c)
						else:
							self.child.write(ch)
							# Print Character
							if curses.ascii.isprint(ch) and not self.__interrupts:
								sys.stdout.write(ch)
								self.child.read_nonblocking(len(ch))
					# EOF
					elif s == 3:
						print self.child.before,
						break
					# Prompt
					else:
						self.buf()
						# Get Input
						self.__default_int()
						query = self.getline(self.child.after)
						self.__ignore_int()
						self.child.sendline(query)
						answ = self.child.read_nonblocking(size = len(query) + len(self.linesep))
				except EOFError:
					self.child.sendeof()
					self.child.expect(pexpect.EOF)
					print self.child.before,
					break
				except KeyboardInterrupt:
					self.__interrupts.append(self.buffered()) 
					self.child.sendcontrol('c')
					continue
				except SystemExit:
					break
		finally:
			if self.child.isalive(): self.child.terminate()


def which(program):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file

	return None

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'Usage: eclwrapper <eclipse executable path> <additional arguments>'
	elif not which(sys.argv[1]):
		print "'" + sys.argv[1] + "' is not a valid path for the ECLiPSe shell executable"
	else:
		eclipse_wrapper = EclWrapper(sys.argv[1], sys.argv[2:])
		eclipse_wrapper()


