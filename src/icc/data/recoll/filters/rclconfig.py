#!/usr/bin/env python
from __future__ import print_function

import locale
import re
import os
import sys
import base64
import platform

class ConfSimple:
    """A ConfSimple class reads a recoll configuration file, which is a typical
    ini file (see the Recoll manual). It's a dictionary of dictionaries which
    lets you retrieve named values from the top level or a subsection"""

    def __init__(self, confname, tildexp = False):
        self.submaps = {}
        self.dotildexpand = tildexp
        try:
            f = open(confname, 'r')
        except Exception as exc:
            #print("Open Exception: %s" % exc, sys.stderr)
            # File does not exist -> empty config, not an error.
            return

        self.parseinput(f)
        
    def parseinput(self, f):
        appending = False
        line = ''
        submapkey = ''
        for cline in f:
            cline = cline.rstrip("\r\n")
            if appending:
                line = line + cline
            else:
                line = cline
            line = line.strip()
            if line == '' or line[0] == '#':
                continue

            if line[len(line)-1] == '\\':
                line = line[0:len(line)-1]
                appending = True
                continue
            appending = False
            #print(line)
            if line[0] == '[':
                line = line.strip('[]')
                if self.dotildexpand:
                    submapkey = os.path.expanduser(line)
                else:
                    submapkey = line
                #print("Submapkey: [%s]" % submapkey)
                continue
            nm, sep, value = line.partition('=')
            if sep == '':
                continue
            nm = nm.strip()
            value = value.strip()
            #print("Name: [%s] Value: [%s]" % (nm, value))

            if not submapkey in self.submaps:
                self.submaps[submapkey] = {}
            self.submaps[submapkey][nm] = value

    def get(self, nm, sk = ''):
        '''Returns None if not found, empty string if found empty'''
        if not sk in self.submaps:
            return None
        if not nm in self.submaps[sk]:
            return None
        return self.submaps[sk][nm]

    def getNames(self, sk = ''):
        if not sk in self.submaps:
            return None
        return list(self.submaps[sk].keys())
    
class ConfTree(ConfSimple):
    """A ConfTree adds path-hierarchical interpretation of the section keys,
    which should be '/'-separated values. When a value is requested for a
    given path, it will also be searched in the sections corresponding to
    the ancestors. E.g. get(name, '/a/b') will also look in sections '/a' and
    '/' or '' (the last 2 are equivalent)"""
    def get(self, nm, sk = ''):
        if sk == '' or sk[0] != '/':
            return ConfSimple.get(self, nm, sk)
            
        if sk[len(sk)-1] != '/':
            sk = sk + '/'

        # Try all sk ancestors as submaps (/a/b/c-> /a/b/c, /a/b, /a, '')
        while sk.find('/') != -1:
            val = ConfSimple.get(self, nm, sk)
            if val is not None:
                return val
            i = sk.rfind('/')
            if i == -1:
                break
            sk = sk[:i]

        return ConfSimple.get(self, nm)

class ConfStack:
    """ A ConfStack manages the superposition of a list of Configuration
    objects. Values are looked for in each object from the list until found.
    This typically provides for defaults overriden by sparse values in the
    topmost file."""

    def __init__(self, nm, dirs, tp = 'simple'):
        fnames = []
        for dir in dirs:
            fnm = os.path.join(dir, nm)
            fnames.append(fnm)
            self._construct(tp, fnames)

    def _construct(self, tp, fnames):
        self.confs = []
        for fname in fnames:
            if tp.lower() == 'simple':
                conf = ConfSimple(fname)
            else:
                conf = ConfTree(fname)
            self.confs.append(conf)

    def get(self, nm, sk = ''):
        for conf in self.confs:
            value = conf.get(nm, sk)
            if value is not None:
                return value
        return None

class RclDynConf:
    def __init__(self, fname):
        self.data = ConfSimple(fname)

    def getStringList(self, sk):
        nms = self.data.getNames(sk)
        out = []
        if nms is not None:
            for nm in nms:
                out.append(base64.b64decode(self.data.get(nm, sk)))
        return out
    
class RclConfig:
    def __init__(self, argcnf = None):
        self.config = None
        platsys = platform.system()
        # Find configuration directory
        if argcnf is not None:
            self.confdir = os.path.abspath(argcnf)
        elif "RECOLL_CONFDIR" in os.environ:
            self.confdir = os.environ["RECOLL_CONFDIR"]
        else:
            if platsys == "Windows":
                if "LOCALAPPDATA" in os.environ:
                    dir = os.environ["LOCALAPPDATA"]
                else:
                    dir = os.path.expanduser("~")
                self.confdir = os.path.join(dir, "Recoll")
            else:
                self.confdir = os.path.expanduser("~/.recoll")
        #print("Confdir: [%s]" % self.confdir, file=sys.stderr)
        
        # Also find datadir. This is trickier because this is set by
        # "configure" in the C code. We can only do our best. Have to
        # choose a preference order. Use RECOLL_DATADIR if the order is wrong
        self.datadir = None
        if "RECOLL_DATADIR" in os.environ:
            self.datadir = os.environ["RECOLL_DATADIR"]
        else:
            if platsys == "Windows":
                self.datadir = os.path.join(os.path.dirname(sys.argv[0]), "..")
            else:
                dirs = ("/opt/local", "/usr", "/usr/local")
                for dir in dirs:
                    dd = os.path.join(dir, "share/recoll")
                    if os.path.exists(dd):
                        self.datadir = dd
        if self.datadir is None:
            self.datadir = "/usr/share/recoll"
        #print("Datadir: [%s]" % self.datadir, file=sys.stderr)
        self.cdirs = []
        
        # Additional config directory, values override user ones
        if "RECOLL_CONFTOP" in os.environ:
            self.cdirs.append(os.environ["RECOLL_CONFTOP"])
        self.cdirs.append(self.confdir)
        # Additional config directory, overrides system's, overridden by user's
        if "RECOLL_CONFMID" in os.environ:
            self.cdirs.append(os.environ["RECOLL_CONFMID"])
        self.cdirs.append(os.path.join(self.datadir, "examples"))
        #print("Config dirs: %s" % self.cdirs, file=sys.stderr)
        self.keydir = ''

    def getConfDir(self):
        return self.confdir
    
    def setKeyDir(self, dir):
        self.keydir = dir

    def getConfParam(self, nm):
        if not self.config:
            self.config = ConfStack("recoll.conf", self.cdirs, "tree")
        return self.config.get(nm, self.keydir)
        
class RclExtraDbs:
    def __init__(self, config):
        self.config = config

    def getActDbs(self):
        dyncfile = os.path.join(self.config.getConfDir(), "history")
        dync = RclDynConf(dyncfile)
        return dync.getStringList("actExtDbs")
    
if __name__ == '__main__':
    config = RclConfig()
    print(config.getConfParam("topdirs"))
    extradbs = RclExtraDbs(config)
    print(extradbs.getActDbs())
