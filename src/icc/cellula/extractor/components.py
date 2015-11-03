
from icc.cellula.extractor.interfaces import IExtractor
from zope.interface import implementer, Interface
from zope.component import getUtility
import subprocess as sp
import tempfile
import os, os.path
from collections import OrderedDict
from configparser import ConfigParser

@implementer(IExtractor)
class LibExtractorExtractor(object):
    extractor_binary = 'extract'
    config_section='extractor'
    def __init__(self):
        """Creates extractor object, finds
        'extract' binary path if it is not
        supported ith execpathname.

        Arguments:
        - `execpathname`: path to 'extract' binary,
        if None "which" search is used
        """

        config=getUtility(Interface, "configuration")

        execpathname=config[self.config_section].get('exec_path', None)

        if execpathname == None:
            cp=sp.run(["which",self.extractor_binary], stdout=sp.PIPE, stdin=sp.PIPE)
            if cp.stderr:
                raise RuntimeError(cp.stderr)
            self.extractor=cp.stdout.strip()
        else:
            self.extractor=os.path.join(execpathname, self.extractor_binary)

        # test it
        if not self.test_working():
            raise RuntimeError('cannot determine operability of extract utility')

        self.tmp_path=config[self.config_section].get('tmp_path', tempfile.gettempdir())


    def test_working(self):
        out=self.run('-v')
        return out.startswith('extract')

    def run(self, *params, ignore_err=False, executable=None):
        """Run extract binary and capture its stdout.
        If there is some stderr output, raise exception if
        it is not igored (ignore_err).
        """

        if executable == None:
            executable = self.extractor

        cp=sp.run([executable]+list(params), stdout=sp.PIPE, stderr=sp.PIPE)
        if cp.stderr and not ignore_err:
            raise RuntimeError(cp.stderr.decode('utf-8').strip())
        return cp.stdout.decode('utf-8')

    def extract(self, content, headers=None):
        """Run extractor over content data.
        If headers present use them as additional heuristics."""


        if headers == None:
            headers = {}

        filename=None # headers.get('FileName', None)

        if filename != None:
            filepath=os.path.join(self.tmp_path, filename)
            inf=open(filepath, "w+b")
            tf=False
        else:
            inf=tempfile.NamedTemporaryFile(dir=self.tmp_path)
            filepath=inf.name
            tf=True

        inf.seek(0)
        inf.write(content)
        inf.flush()

        rc=self.do_extract(filepath)

        if not tf:
            inf.close()
            os.remove(filepath)

        del inf

        return rc

    def do_extract(self, filepath):
        """Run the extractor over temporal
        file and process output.
        """

        out=self.run(filepath)

        lines=out.split("\n")

        answer=OrderedDict()
        for line in lines:
            line=line.strip()
            if line.startswith("Keywords for file"):
                continue
            if len(line)==0:
                continue
            key,value=line.split(" - ")
            key=key.strip().replace(" ","-")
            value=value.strip()

            vals=answer.setdefault(key,OrderedDict())
            vals[value]=value

        new_a=OrderedDict()
        for k,v in answer.items():
            l=list(v)
            if len(l)==1:
                l=l[0]
            new_a[k]=l

        return new_a


@implementer(IExtractor)
class TrackerExtractor(LibExtractorExtractor):
    """Extractor of metadata and text body.
    """
    extractor_binary="tracker-extract"
    config_section="tracker"

    def test_working(self):
        out=self.run('-V')
        out=out.strip()
        return out.startswith("Tracker")

    def do_extract(self, filepath):
        """Run the extractor over temporal
        file and process output.
        """

        try:
            out=self.run('-f', filepath)
        except RuntimeError:
            return {}

        answer=OrderedDict()
        lines=out.splitlines()
        sparql_item=False
        for line in lines:
            line=line.rstrip()
            ll=line.lstrip()
            if ll.startswith("SPARQL item:"):
                sparql_item=True
                continue
            elif not sparql_item:
                continue
            elif ll.startswith("--"):
                continue
            elif ll.startswith("SPARQL where"):
                break
            comps = ll.split(maxsplit=1)
            if len(comps)==0:
                continue
            if len(comps)==1:
                print ("Tracker: 1-size comp:", comps[0][:60])
                continue
            p, o = comps
            if p=='a':
                p="rdf:type"
            if o.startswith("?"):
                continue
            o=o.rstrip(";").rstrip()
            if o.startswith("["):
                o=o.lstrip("[").lstrip()
            if o.endswith("]"):
                o=o.rstrip("]").rstrip()
            try:
                o=int(o)
                answer[p]=o
                continue
            except ValueError:
                pass
            try:
                o=float(o)
                answer[p]=o
                continue
            except ValueError:
                pass
            # do something with date
            #print (p, str(o)[:60])
            if p.startswith("nie:plainTextContent"):
                p='text-body'
                o=o.strip("'"+'"')

            answer[p]=o

        return answer

# Recoll extractor
# /usr/share/recoll/filters/

@implementer(IExtractor)
class RecollExtractor(object):
    extractor_binary=None
    config_section="recoll"

    def __init__(self):
        """
        """

        config=getUtility(Interface, 'configuration')

        mime_map=config[self.config_section]['mimeconf']
        self.filterdir=config[self.config_section]['filter_dir']
        self.tmp_path=config[self.config_section].get('tmp_path', tempfile.gettempdir())

        self.config=ConfigParser(strict=False)
        conf_s="[DEFAULT]\n"+open(mime_map).read()
        self.config.read_string(conf_s)

    def extract(self, content, headers):
        """Extract data and metadata from content
        using headers as heuristic data.

        Arguments:
        - `content`: Content itself to extract data from.
        - `headers`: Recognized and supplied metadata.
        """

        answer=OrderedDict()

        content_type=headers.get('Content-Type', None)
        mimetype=headers.get('mimetype', None)

        mimes=set((content_type,))
        if type(mimetype)==list:
            mimes.update(mimetype)
        else:
            mimes.add(mimetype)
        mimes.discard(None)

        inf=tempfile.NamedTemporaryFile(dir=self.tmp_path)
        filepath=inf.name
        tf=True

        inf.seek(0)
        inf.write(content)
        inf.flush()


        text=''
        for mimetype in mimes:
            new_text=self.extract_mime(content, headers, mimetype, filepath)
            if len(new_text)>len(text):
                text=new_text
        del inf
        if text:
            return {'text-body':text}
        else:
            return {}

    def extract_mime(self, content, headers, mimetype, tmpfile):
        index=self.config['index']
        try:
            script=index[mimetype]
        except KeyError as e:
            return ''

        print ("Filter:", script)
        try:
            way, cmd = script.split()
        except ValueError:
            cmd=script

        if cmd=='internal':
            return content.decode('utf8')

        executable = os.path.join(self.filterdir, cmd)

        out = ''
        if way == 'exec':
            try:
                out=self.run(tmpfile,executable=executable)
            except RuntimeError:
                out=""
        else:
            print ('WARNING:Non-implemented filer class %s for script %s' % (way, script))

        return out

    def run(self, *params, ignore_err=False, executable=None):
        """Run extract binary and capture its stdout.
        If there is some stderr output, raise exception if
        it is not igored (ignore_err).
        """

        if executable == None:
            raise ValueError("no executable")

        cp=sp.run([executable]+list(params), stdout=sp.PIPE, stderr=sp.PIPE)
        if cp.stderr and not ignore_err:
            err=cp.stderr.decode('utf-8').strip()
            raise RuntimeError(err)
        return cp.stdout.decode('utf-8')
