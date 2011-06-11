import re
import codecs
from optparse import OptionParser

from gtparse import parse

def build_parser():
    usage = '%prog [OPTION] [POFILE...]'
    description = 'write POFILEs to stdout'

    p = OptionParser(usage=usage,
                     description=description)
    p.add_option('--encode', metavar='ENCODING',
                 dest='encoding',
                 help='convert FILEs to ENCODING and update header')
    return p
    

def main():
    p = build_parser()
    
    opts, args = p.parse_args()
    
    for arg in args:
        cat = parse(open(arg))
        
        if opts.encoding is not None:
            src_encoding = cat.encoding
            codecinfo = codecs.lookup(opts.encoding)

            # should result in a canonical/transferable name even if
            # people don't specify dashes or other things in the way
            # gettext likes
            dst_encoding = codecinfo.name

            header = cat.header

            lines = header.msgstr.split('\\n')
            for i, line in enumerate(lines):
                if line.startswith('Content-Type:'):
                    break
            else:
                p.error('Cannot find Content-Type in header')
            line = line.replace('charset=%s' % src_encoding, 
                                'charset=%s' % dst_encoding)
            lines[i] = line
            header.msgstr = '\\n'.join(lines)
            
            for msg in cat:
                print msg.tostring().decode(src_encoding).encode(dst_encoding)
            for obs in cat.obsoletes:
                print obs.decode(src_encoding).encode(dst_encoding),
                #print obs.tostring().decode(src_encoding).encode(dst_encoding)
        else:
            for msg in cat:
                print msg.tostring()
            for obs in cat.obsoletes:
                print obs.tostring()
                #print obs.tostring()