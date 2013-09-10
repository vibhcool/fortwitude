import re
import sys

pr0n_words=re.compile(r"(fucke?d?i?n?g?|fingering|chicks?|dicks?|penis|cocks?|tits?|pussy|cunt|clit|ass|anal|xxx|sex|shit|twat|porn|cumshot|clitoris)", re.IGNORECASE)

def match_words(text):
    return pr0n_words.search(text)


