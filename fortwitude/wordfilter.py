import re
import sys
import os

# Let us disguise them
pr0n_words_d=['shpxr?q?v?a?t?', 'svatrevat', 'puvpxf?', 'qvpxf?', 'cravf', 'pbpxf?', 'gvgf?', 'chffl', 'phag', 'pyvg', 'nff', 'nany', 'kkk', 'frk', 'fuvg', 'gjng', 'cbea', 'phzfubg', 'pyvgbevf']

other_words_d = ['avttn?', 'oebgun']
prude_words_d = ['ubeal', 'ovgpu', 'qnza', 'lhpx', 'fuvg','snt','yrfob','yrfovna']

# general stuff we want to avoid.
general_words = ['hairy','bikers?','jets?','crazy','crazier','craziest',
                 'booty','tattoo','stfu','whore','shitt?','demo','sorry$\.?',
                 'twitter','ipad','ipod','kindle','mac','macintosh',
                 'iphone','walkman','kewl','meds?','whata','mom','mum',
                 'pop','miley','cyrus','britney','spears','weed','drug',
                 'ganja','marijuana','google','yahoo','album','rocks',
                 'hifi','shoulda','woulda','coulda','sucks','weekend$\.?',
                 'nah','yeah','justin','bieber','rihanna','kim','kardashian',
                 'tweets?','disney','mickey','tho','noot','sittin','rapper',
                 'guna','ny','pls','\w+in\s+','sick\.?','em','unfollow',
                 'outta','mikey','gaga','elle','uh','uhn','booger',
                 'ew','eww','soo','\w+nna\s+','cos','tryna','cuzz',
                 'cuss','haha','scooters?','smoothies?','heck','piss',
                 'cuz','craps?','sneeze','farts?','horror','moan','meth',
                 'is black','am black',"'m black",'wifi','router','stuffs']

pr0n_words = re.compile('|'.join(x.encode('rot13') for x in pr0n_words_d))
other_words = re.compile('|'.join(x.encode('rot13') for x in other_words_d))
prude_words = re.compile('|'.join(x.encode('rot13') for x in prude_words_d))
general_words_re = re.compile('|'.join(general_words))

www_lang = {s.strip().lower():1 for s in open(os.path.expanduser("~/.fortwitude_en/wwwlang")).read().split()}

def match_words(text, prude_mode=True):
    text = text.lower()
    return any((pr0n_words.search(text),
                other_words.search(text),
                general_words_re.search(text),
                prude_mode and prude_words.search(text),
                any((x.lower() in www_lang for x in text.split()))))


