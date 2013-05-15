#!/usr/bin/env python
"""
podiff -- A gettext diff module in Python
Copyright (C) 2009-2011 Kenneth Nielsen <k.nielsen81@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import sys
from optparse import OptionParser
from difflib import unified_diff
from pyg3t.gtparse import parse
from pyg3t import __version__


class PoDiff:

    """Description of the PoDiff class"""

    def __init__(self, out, show_line_numbers=False, colors=False):
        """Initialize class variables

        Keywords:
        out        A file like object that the output will be printed to
        show_line_numbers
                   boolean, whether to show the line numbers from the new
                   catalog object in a header line above each diff piece
        """
        self.out = out
        self.number_of_diff_chunks = 0
        self.show_line_numbers = show_line_numbers
        self.colors = colors

    @staticmethod
    def catalogs_have_common_base(old_cat, new_cat):
        """Check if catalogs has common base

        Keywords:
        old_cat    old catalog
        new_cat    new catalog
        """
        # Perform checks of whether the files have common base
        if len(old_cat) != len(new_cat):
            return False

        for old_msg, new_msg in zip(old_cat, new_cat):
            if old_msg.key != new_msg.key:
                return False

        return True

    def diff_catalogs_relaxed(self, old_cat, new_cat, full_diff=False):
        """Diff catalogs relaxed. I.e. accept differences in base.

        Keywords:
        old_cat    old catalog
        new_cat    new catalog
        full_diff  boolean, show msg's unique to old_cat
        """
        dict_old_cat = old_cat.dict()

        encoding = (old_cat.encoding, new_cat.encoding)\
            if new_cat.encoding != old_cat.encoding else (None, None)

        # Make diff for all the msg's in new_cat
        for new_msg in new_cat:
            if new_msg.key in dict_old_cat:
                self.diff_two_msgs(dict_old_cat[new_msg.key], new_msg,
                                   fname=new_cat.fname, enc=encoding)
            else:
                self.diff_one_msg(new_msg, is_new=True, fname=new_cat.fname,
                                  enc=encoding)

        # If we are making the full diff, diff the entries that are only
        # present in old file
        if full_diff:
            dict_new_cat = new_cat.dict()
            only_old = [key for key in dict_old_cat if key not in
                        dict_new_cat]

            for key in only_old:
                self.diff_one_msg(dict_old_cat[key], is_new=False,
                                  fname=old_cat.fname, enc=encoding)

        self.print_status()

    def diff_catalogs_strict(self, old_cat, new_cat):
        """Diff catalogs strict. I.e. enforce common base

        Keywords:
        old_cat    old catalog
        new_cat    new catalog
        """
        encoding = (old_cat.encoding, new_cat.encoding)\
            if new_cat.encoding != old_cat.encoding else (None, None)

        for old_msg, new_msg in zip(old_cat, new_cat):
            self.diff_two_msgs(old_msg, new_msg, fname=new_cat.fname,
                               enc=encoding)
        self.print_status()

    def diff_two_msgs(self, old_msg, new_msg, fname=None, enc=(None, None)):
        """Produce diff between two messages

        Keywords:
        old_msg    old message
        new_msg    new message
        new_cat    new catalog (Used to get the filename for the line number
                   header)
        """

        # re-encode old_msg.msgstrs and -.get_comments('# ') for comparison
        if enc != (None, None):
            re_enc_old_msgstrs = [line.decode(enc[0]).encode(enc[1])
                                  for line in old_msg.msgstrs]
            re_enc_old_comments = [line.decode(enc[0]).encode(enc[1])
                                  for line in old_msg.get_comments('# ')]
        else:
            re_enc_old_msgstrs = old_msg.msgstrs
            re_enc_old_comments = old_msg.get_comments('# ')

        # Check if the there is a reason to diff.
        # NOTE: Last line says we always show header
        if old_msg.isfuzzy is not new_msg.isfuzzy or\
                re_enc_old_msgstrs != new_msg.msgstrs or\
                re_enc_old_comments != new_msg.get_comments('# ') or\
                new_msg.msgid == "":

            if self.show_line_numbers:
                print >> self.out, self.__print_lineno(new_msg, fname)

            # Make the diff
            if enc != (None, None):
                old_lines = [line.decode(enc[0]).encode(enc[1],
                                                        'replace')
                             for line in old_msg.meta['rawlines']]
            else:
                old_lines = old_msg.meta['rawlines']

            diff = list(unified_diff(old_lines, new_msg.meta['rawlines'],
                                     n=10000))

            if len(diff) == 0 and new_msg.msgid == "":
                self.__print_header(new_msg)
            else:
                # Print the result, without the 3 lines of header
                print >> self.out, ''.join(diff[3:])

            if new_msg.msgid != "":
                self.number_of_diff_chunks += 1

    def __print_header(self, msg):
        """ Prints out the header when there is no diff in it """
        for line in msg.meta['rawlines']:
            print >> self.out, ' ' + line,
        print >> self.out

    def diff_one_msg(self, msg, is_new, fname=None, enc=(None, None)):
        """Produce diff if only one entry is present

        Keywords:
        msg        message
        cat        catalog
        is_new     boolean
        """
        if self.show_line_numbers:
            print >> self.out, self.__print_lineno(msg, fname)

        # Make the diff
        if enc != (None, None) and not is_new:
            msg_lines = [line.decode(enc[0]).encode(enc[1], errors='replace')
                         for line in msg.meta['rawlines']]
        else:
            msg_lines = msg.meta['rawlines']

        if is_new:
            diff = list(unified_diff('', msg_lines, n=10000))
        else:
            diff = list(unified_diff(msg_lines, '', n=10000))

        # Print the result without the 3 lines of header
        print >> self.out, ''.join(diff[3:])  # .encode('utf8')
        self.number_of_diff_chunks += 1

    @staticmethod
    def __print_lineno(msg, fname=None):
        """Print line number and file name header for diff of msg pairs"""
        lineno = msg.meta['lineno'] if 'lineno' in msg.meta else 'N/A'
        return ('--- Line %d (%s) ' % (lineno, fname)).ljust(32, '-')

    def print_status(self):
        """Print the number of diff pieces that have been output"""
        sep = ' ' + '=' * 77
        print >> self.out, sep
        print >> self.out, " Number of messages: %d" % \
            self.number_of_diff_chunks
        print >> self.out, sep


def __build_parser():
    """ Builds the options """
    description = ('Prints the difference between two po-FILES in pieces '
                   'of diff output that pertain to one original string. '
                   )

    usage = ('%prog [OPTIONS] ORIGINAL_FILE UPDATED_FILE\n\n'
             'Use - as file argument to use standard in')
    parser = OptionParser(usage=usage, description=description,
                          version=__version__)

    parser.add_option('-l', '--line-numbers', action='store_true',
                      default=True, dest='line_numbers',
                      help='prefix line number of the msgid in the original '
                      'file to the diff chunks')
    parser.add_option('-m', '--no-line-numbers', action='store_false',
                      dest='line_numbers',
                      help='do not prefix line number (opposite of -l)')
    parser.add_option('-o', '--output',
                      help='file to send the diff output to, instead of '
                      'standard out')
    parser.add_option('-r', '--relax', action='store_true', default=False,
                      help='allow for files with different base, i.e. '
                      'where the msgids are not pairwise the same. But still '
                      'make the output proofread friendly.')
    parser.add_option('-s', '--strict', action='store_false', dest='relax',
                      help='do not allow for files with different base '
                      '(opposite of -r)')
    parser.add_option('-f', '--full', action='store_true', default=False,
                      help='like --relax but show the full diff including the '
                      'entries that are only present in the original file')
    parser.add_option('-c', '--color', action='store_true', default=False,
                      help='make a wordwise diff and use markers to highlight '
                      'it')
    return parser


def main():  # pylint: disable-msg=R0912
    """The main function loads the files and outputs the diff"""

    option_parser = __build_parser()
    opts, args = option_parser.parse_args()

    # We need exactly two files to proceed
    if len(args) != 2:
        option_parser.error('podiff takes exactly two arguments')

    # Open file for writing, if it is not one of the input files
    if opts.output:
        if opts.output in (args[0], args[1]):
            option_parser.error('The output file you have specified is the '
                                'same as one of the input files. This is not '
                                'allowed, as it may cause a loss of work.')

        try:
            out = open(opts.output, 'w')
        except IOError, err:
            print >> sys.stderr, ('Could not open output file for writing. '
                                  'open() gave the following error:')
            print >> sys.stderr, err
            raise SystemExit(4)
    else:
        out = sys.stdout

    # Get PoDiff instanse
    podiff = PoDiff(out, opts.line_numbers, opts.color)

    # Load files into catalogs
    try:
        if args[0] == '-':
            cat_old = parse(sys.stdin)
        else:
            cat_old = parse(open(args[0]))

        if args[1] == '-':
            cat_new = parse(sys.stdin)
        else:
            cat_new = parse(open(args[1]))
    except IOError, err:
        print >> sys.stderr, ('Could not open one of the input files for '
                              'reading. open() gave the following error:')
        print >> sys.stderr, err
        raise SystemExit(5)

    # Diff the files
    if opts.relax or opts.full:
        podiff.diff_catalogs_relaxed(cat_old, cat_new, opts.full)
    else:
        if not podiff.catalogs_have_common_base(cat_old, cat_new):
            option_parser.error('Cannot work with files with dissimilar base, '
                                'unless the relax option (-r) or the full '
                                'options (-f) is used.\n\nNOTE: This is not '
                                'recommended..!\nMaking a podiff for '
                                'proofreading should happen between files '
                                'with similar base, to make the podiff easier '
                                'to read.')

        podiff.diff_catalogs_strict(cat_old, cat_new)

    return


if __name__ == '__main__':
    main()
