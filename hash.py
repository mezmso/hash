#!/usr/bin/env python

import sys
import os
import select
import shlex
import readline
import signal

from curses import ascii

import dtach
import term
import linebuf
import alias


def clear_screen():
    os.write(1, '\33[H\33[J')

class Hash(object):
    HASH_KEY=ascii.ctrl('\\')
    def __init__(self):
        self.line = linebuf.LineBuf()
        self.term = term.Terminal(0)
        self.aliascmds = {}

    def completer(self, text, state):
        matches = [s for s in self.cmdtab.keys() if s.startswith(text)]

        try:
            return matches[state]
        except IndexError:
            return None

    def load_commands(self):
        import command
        import commands
        import filetransfer

        self.cmdtab = {}
        for cmd in command.list_commands():
            self.cmdtab[ cmd.name ] = cmd(self)

    def builtin_bang(self, line):
        os.system(line[1:])

    def builtin_alias(self, line):
        line = line[5:].strip()
        if not line.strip():
            for k,v in self.aliascmds.iteritems():
                print "%s = %s" % (k,v)
        else:
            alias_cmd, sh_cmd = line.split('=', 1)
            self.aliascmds[ alias_cmd ] = sh_cmd
            self.cmdtab[alias_cmd] = alias.Alias(self, sh_cmd)

    def builtin_command(self, line):
        argv = shlex.split(line)
        if argv[0] in self.cmdtab:
            try:
                self.cmdtab[argv[0]].process(argv)
            except Exception, e:
                print 'Error!', e
        else:
            print '[ErrorBetweenKeyboardAndChair] Unknown command: %s' % argv[0]

    def process(self, line):
        line = line.lstrip()
        if line[0] == '!':
            self.builtin_bang(line)
        elif line.startswith("alias") and (len(line) == 5 or line[5] == ' '):
            self.builtin_alias(line)
        else:
            self.builtin_command(line)

    def attach(self, hashname):
        self.master = dtach.attach(hashname)
        self.load_commands()

    def spawn(self, hashname, command, args=[], env=None):
        dtach.dtach(hashname, command, args, env)
        while 1:
            import time
            if not os.access(hashname, os.R_OK):
                time.sleep(0.01)
                continue
            self.master = dtach.attach(hashname)
            break
        self.load_commands()

    def interact(self):
        self.term.raw()
        try:
            self.loop()
        except (IOError, OSError):
            self.term.cooked()
        try:
            self.master.close()
        except (OSError):
            pass

    def stdin_read(self, fd):
        c = os.read(fd, 1)
        if c == self.HASH_KEY:
            self.line.blank()
            self.term.cooked()
            readline.set_completer(self.completer)

            try:
                line = raw_input('hash% ').lstrip()
                self.process(line)
            except:
                pass

            self.term.raw()
            self.line.display()
            return ''
        else:
            return c

    def loop(self):
        while 1:
            r,w,x = select.select([self.master, 0], [], [])
            if self.master in r:
                data = self.master.read(4096)
                self.line.process(data)
                os.write(1, data)
            if 0 in r:
                data = self.stdin_read(0)
                while data != '':
                    n = self.master.write(data)
                    data = data[n:]

def parse_opts(argv):
    parser = optparse.OptionParser()
    parser.add_option("-a", "--attach", dest="attach",
            help="attach to SOCKNAME")
    parser.add_option('-v', '--verbose', dest="verbose",
            action="store_true", default=False)
    opt, args = parser.parse_args(argv)

    if opt.attach:
        opt.hashname = opt.attach
    else:
        opt.hashname = "/tmp/hash.%d" % os.getpid()

    if opt.verbose:
        print "Using:", opt.hashname

    if args:
        command = args

def main(argv):

    if argv[1:]:
        hashname = argv[1]
    else:
        hashname =  "/tmp/hash.%d" % os.getpid()

    readline.parse_and_bind('tab: complete')
    hsh = Hash()
    hsh.spawn(hashname, "/bin/sh -i", env=os.environ)
    hsh.interact()

if __name__ == "__main__":
    t = term.Terminal(0)
    t.save()
    try:
        main(sys.argv)
    finally:
        t.restore()
