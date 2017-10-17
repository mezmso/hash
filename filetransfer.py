#!/usr/bin/env python

import os
import binascii
import command

'''
class FtpCommands(object):
    def __init__(self, shell):
        self.shell = shell
    def _get_remote_file(self, fname):
        cmd = "od -tx1 %s|sed -e 's/[0123456789abcdefABCDEF]*[ ]*//'"
        self.shell.init()
        enc_buf = self.shell.run(cmd % fname)
        self.shell.fini()
        return binascii.unhexlify(''.join(enc_buf.split()))
    def _put_remote_file(self, fname, buf):
        buf = binascii.hexlify(buf)

        enc_data = []
        for i in range(0, len(buf), 32):
            encoded=''
            for i in range(0, 32, 2):
                encoded += '\\x' + buf[i:i+1]
            enc_data.append( encoded )

        # grab the last bit
        encoded = ''
        rem = len(buf) % 32
        for i in range(len(buf)/32, rem, 2):
            encoded += '\\x' + buf[i:i+1]
        enc_data.append(encoded)

        self.shell.init()
        self.shell.run('echo > %s' % fname)
        for enc in enc_data:
            self.shell.run('echo -e -n "%s" >> %s' % (enc, fname))
        self.shell.fini()

    def get_file(self, rname, lname):
        buf = self._get_remote_file(rname)
        open(lname, 'w').write(buf)

    def put_file(self, buf, fname):
        buf = binascii.hexlify(buf)
        self._put_remote_file(buf, fname)
'''
class PutFile(command.Command):
    '''
    Put file on a remote system
    Note: This utility does not work with
    standard /bin/sh as its echo program simply
    outputs all arguments

    A solution to this would be to reimplement
    the process with base64
    '''
    name = 'put'
    help = 'upload a file.'
    def _put_file(self, buf, fname):
        buf = binascii.hexlify(buf)

        enc_data = []

        for l in [buf[i:i+32] for i in range(0, len(buf), 32)]:
            enc = ''
            for i in range(0, len(l), 2):
                enc += '\\x' + l[i:i+2]
            enc_data.append(enc)

        self.shell.init()
        # clear file
        self.shell.run('echo > %s' % fname)
        for enc in enc_data:
            self.shell.run('echo -e -n "%s" >> %s' % (enc, fname))
        self.shell.fini()

    def put_file(self, lname, rname):
        buf = open(lname).read()
        self._put_file(buf, rname)

    def execute(self, *args):
        if not args:
            print "put <local file> [<remote file>]"
            return
        if len(args) == 1:
            lname = args[0]
            rname = os.path.basename( args[0] )
        else:
            lname = args[0]
            rname = args[1]
        self.put_file(lname, rname)

class GetFile(command.Command):
    name = 'get'
    help = 'download a file'
    def _get_file(self, fname):
        cmd = "od -tx1 %s|sed -e 's/[0123456789abcdefABCDEF]*[ ]*//'"
        #cmd = "od -t x1 %s | sed -e 's/[0123456789abcdefABCDEF]*[ ]*//' | sed -e 's/[ ]//g'"
        enc_buf = self.shell.system(cmd % fname)
        return binascii.unhexlify(''.join(enc_buf.split()))

    def get_file(self, rname, lname):
        buf = self._get_file(rname)
        open(lname, 'w').write(buf)

    def execute(self, *args):
        if not args:
            print "get <remote file> [<local file>]"
            return
        elif len(args) == 1:
            rname = args[0]
            lname = os.path.basename( rname )
        else:
            rname = args[0]
            lname = args[1]

        self.get_file(rname, lname)


#class FileTransfer(command.Command):
    #name = 'ftp'
    #help = 'inline file transfer'
    # command_loop(): ...
    #   get
    #   put
    #   mget
    #   mput
