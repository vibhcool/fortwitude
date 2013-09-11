import re
import sys

# Let us disguise them
pr0n_words_d=['shpxr?q?v?a?t?', 'svatrevat', 'puvpxf?', 'qvpxf?', 'cravf', 'pbpxf?', 'gvgf?', 'chffl', 'phag', 'pyvg', 'nff', 'nany', 'kkk', 'frk', 'fuvg', 'gjng', 'cbea', 'phzfubg', 'pyvgbevf']

other_words_d=['avttn?', 'oebgun']
pr0n_words = re.compile('|'.join(x.encode('rot13') for x in pr0n_words_d))
other_words = re.compile('|'.join(x.encode('rot13') for x in other_words_d))

def match_words(text):
    return any((pr0n_words.search(text),
                other_words.search(text)))


