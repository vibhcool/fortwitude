"""
Fortwitude - Fortune (like) cookies from Twitter streams.

"""

from twitter import *
from settings import *
import sys
import os
from itertools import takewhile
import string
import re
import cPickle
import datetime
import random
import argparse
import trigrams
import wordfilter
import threading
import time
import HTMLParser
import signal

from contextlib import contextmanager, nested

url_re = re.compile(r'https?\:\/\/', re.IGNORECASE)
# 2 or more spaces
double_space_re = re.compile(r'\s{2,}')
# Words like B1, C25 ABC123 going2use time2do etc.
words_digits = re.compile(r'[a-zA-Z]+\d+[a-zA-Z]*')
# * inside words like f*ck, sh*t etc.
starred = re.compile(r'[a-zA-Z]+\*[a-zA-Z]+')

@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass

class FakeProgressMeter(threading.Thread):
    """ Fake progress meter on the console """

    def __init__(self):
        self.flag = False
        threading.Thread.__init__(self, None, None,'progress')

    def run(self):

        while not self.flag:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(random.choice(range(1,5)))

    def stop(self):
        self.flag = True
        
class TwitterWrapper(object):
    """ Wrapper class for twitter actions """

    def __init__(self):
        self.credfile = os.path.expanduser("~/.fortwitudeauth")     
        self.get_credentials()
        
    def get_credentials(self):
        """ Get/create twitter OAuth credentials """
        
        if not os.path.exists(self.credfile):
            oauth_dance("fortwitude", KEY,SECRET,self.credfile)

        token, secret = read_token_file(self.credfile)
        self.twitter = Twitter(auth=OAuth(token, secret, KEY, SECRET))
        self.twitter_s = TwitterStream(auth=OAuth(token, secret, KEY, SECRET))

    def get_status(self, api):
        """ Return the status for the given API type """

        statuses = []
        
        entity = self.twitter
        if api=='sample':
            entity = self.twitter_s

        return getattr(getattr(entity,'statuses'), api).__call__()
    
class Fortwitude(object):
    """ Fortune cookies with Twitter """
    
    def __init__(self,
                 timeline='public',
                 live=False,
                 sample=50,
                 ttl=1440,
                 lang='en',
                 minwords=8,
                 verbose=False):
        
        self.live= live
        self.sample = sample
        self.verbose = verbose
        self.twitter = TwitterWrapper()
        # Source of tweets
        self.source = timeline
        # TTL Delta for cache in minutes
        self.tdelta = datetime.timedelta(minutes=ttl)
        # Tweet stream
        self.tweets = []
        # Min words in a tweet
        self.minwords = minwords
        # htmlparser to unescape stuff
        self.hparse = HTMLParser.HTMLParser()
        # Sample size
        # Mapping of source to twitter API
        self.source_api = {'public': 'sample',
                           'home': 'home_timeline'}

        # Tweets store
        self.store = os.path.expanduser("~/.fortwitudes")
        self.firsttime = not os.path.exists(self.store)
        # Cache
        self.cache = []
        # English language support is implicit.
        self.engram = trigrams.Trigram(os.path.expanduser('~/.fortwitude_en/1lncn10.txt'))
        self.progress = FakeProgressMeter()
        self.progress.setDaemon(True)
        # Flag to quit
        self.flag = False

    def filter(self, text):
        """ Return True if a tweet is a candidate for fortune
        cookie, False otherwise """

        text = text.strip()
        # Even spacing ! - people who type carefully only.
        
        checks = all((not '@' in text,
                      not '#' in text,
                      # People who start their tweets with lower case
                      # are not serious in general ;)
                      text[0].isupper(),
                      # Skip questions, exclamations
                      # text[-1] not in list('?,!(),:;'),
                      text[-1] == '.',
                      # But we dont want ellipsis
                      not text.endswith('..'),
                      # Texts starting with I are normally about oneself,
                      not text.startswith('I '),
                      not double_space_re.search(text),
                      not words_digits.search(text),
                      not starred.search(text),
                      not url_re.search(text),
                      len(text.split())>=self.minwords,
                      not wordfilter.match_words(text)))
            
        if not checks:
            return False
                     
        # For the time being - keep only ascii stuff
        try:
            text.encode('iso-8859-1')
            ascii = True
        except UnicodeEncodeError:
            ascii = False

        # Only english
        gram = trigrams.Trigram(text)
        # Cut off is 0.20
        sim = gram.similarity(self.engram)
        lang = sim >= 0.20
        # print 'Lang=>',sim,text
        
        return all((ascii, lang))

    @staticmethod
    def parse_args():
        """ Parse command line arguments """

        parser = argparse.ArgumentParser(description="Fortwitude - Fortune cookies from Twitter")
        parser.add_argument('-t',dest='timeline',default='public',help='Source timeline to use (default public)')
        parser.add_argument('-l',dest='live',default=False,action='store_true',help='Force to use twitter live (default uses cache if available)')
        parser.add_argument('-s',dest='sample',default=50,type=int,help='Size of twitter messages used to sample (default 50)')
        parser.add_argument('-w',dest='minwords',default=8,type=int,help='Minimum words in a tweet to select it (default 5)')
        parser.add_argument('-v',dest='verbose',default=False,action='store_true',help='Be verbose')
        args = parser.parse_args()
        return args
        
    def build_stream(self):
        """ Build a stream of tweets for making fortune cookies """
        
        tweets = []

        self.message('Building stream of size',self.sample,'...')

        for tweet in takewhile(lambda x: len(tweets)<self.sample,
                               self.twitter.get_status(self.source_api[self.source])):
            if self.flag: break
            
            try:
                tweet_text = tweet['text']
                user = tweet.get('user',{}).get('screen_name', '')
                if self.filter(tweet_text):
                    self.message('Tweet',len(tweets)+1,':',tweet_text)
                    tweets.append((self.hparse.unescape(tweet_text), user))
            except KeyError:
                pass

        self.inform("built content pool of size",len(tweets))
        self.message('built stream.')
        return tweets

    def get_cache(self):
        """ Return cached tweet stream if TTL not expired """

        with ignored(OSError, IOError):
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(self.store))
            if (mtime >= datetime.datetime.now() - self.tdelta):
                # Sufficiently up to date
                self.message("Loading cache.")
                self.cache = cPickle.load(open(self.store))
                self.message("Size of cache is",len(self.cache))
                return self.cache

    def write_cache(self, tweets):
        """ Save tweets into local cache """

        with ignored(Exception,):
            # Keep appending...
            self.cache += tweets
            self.inform("writing cache.")
            cPickle.dump(self.cache, open(self.store,'w'))

    def message(self, *msgs):
        """ Print messages """
        
        if self.verbose:
            try:
                print ' '.join(str(x) for x in msgs)
            except:
                pass

    def inform(self, *msgs):
        """ Print messages if first time """

        if self.firsttime or self.live:
            try:
                print ' '.join(str(x) for x in msgs)
            except:
                pass

    @contextmanager
    def timer(self, msg):
        """ Time your function """

        t1 = time.time()
        yield
        t2 = time.time()
        print msg,'completed in %.2f' % (t2-t1),'seconds.'
        
    def fortune(self):
        """ Get a fortune cookie from twitter """

        self.inform("\nFortwitude is starting up...")
        self.inform("Using",self.source,"timeline as source timeline...")
        self.inform("Sampling",self.sample,"tweets for random pool....")
        
        # If live, turn on verbose mode
        source = self.get_cache()
        
        self.inform('Rebuilding content pool from twitter stream....')
            
        if self.live or (not source):

            with self.timer('stream'):
                self.inform("querying twitter and building content from timeline...")
                if not self.verbose:
                    self.progress.start()
            
                # Cache might not exist or expired
                source = self.build_stream()
                if not self.verbose:
                    self.progress.stop()
            
            self.inform("built content.")           
            # Write cache
            self.write_cache(source)
        else:
            self.message('-- from cache --')
            
        if source:
            # print source
            mesg, user = random.choice(source)
            user = ((not user) and 'Unknown') or user
            print ' - '.join((mesg, user)) + '\n'


    def sighandler(self, signum, frame):
        """ Signal handler """

        print 'Interrupted.',signum
        if self.progress.is_alive():
            self.progress.stop()
            
        self.flag = True
        time.sleep(5)
        print 'Quitting.'

        
if __name__ == "__main__":
    args = Fortwitude.parse_args()
    f = Fortwitude(**args.__dict__)
    # Set up signal handlers
    signal.signal(signal.SIGINT, f.sighandler)
    f.fortune()
