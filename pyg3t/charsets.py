from codecs import lookup


# Encodings taken verbatim from
# https://www.gnu.org/software/gettext/manual/html_node/Header-Entry.html
_gettext_encodings = set("""
ASCII, ISO-8859-1, ISO-8859-2, ISO-8859-3, ISO-8859-4, ISO-8859-5,
ISO-8859-6, ISO-8859-7, ISO-8859-8, ISO-8859-9, ISO-8859-13,
ISO-8859-14, ISO-8859-15, KOI8-R, KOI8-U, KOI8-T, CP850, CP866, CP874,
CP932, CP949, CP950, CP1250, CP1251, CP1252, CP1253, CP1254, CP1255,
CP1256, CP1257, GB2312, EUC-JP, EUC-KR, EUC-TW, BIG5, BIG5-HKSCS, GBK,
GB18030, SHIFT_JIS, JOHAB, TIS-620, VISCII, GEORGIAN-PS,
UTF-8""".replace(',', ' ').split())


_encoding_map = {}
for name in _gettext_encodings:
    try:
        codec_info = lookup(name)
    except LookupError:
        pyname = None
    else:
        pyname = codec_info.name
    _encoding_map[pyname] = name


def get_gettext_encoding_name(name):
    codec_info = lookup(name)
    pyname = codec_info.name
    gettextname = _encoding_map[pyname]
    if gettextname is None:
        raise ValueError('Unregocnized encoding %s.' % name)
    return gettextname


# This function fails when run from the same directory for some reason
# Some namespace clash I guess.
def main():
    for name in sorted(_gettext_encodings):
        try:
            codec_info = lookup(name)
        except LookupError:
            print('Unregocnized: >>>  %s <<<' % name)
        else:
            pyname = codec_info.name
            print('%s -> %s' % (pyname, name))


if __name__ == '__main__':
    main()
