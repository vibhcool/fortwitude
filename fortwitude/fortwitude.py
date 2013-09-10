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

from contextlib import contextmanager, nested

url_re = re.compile(r'https?\:\/\/', re.IGNORECASE)

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

    def filter(self, text):
        """ Return True if a tweet is a candidate for fortune
        cookie, False otherwise """

        text = text.strip()
        
        checks = all((not '@' in text,
                      not '#' in text,
                      # People who start their tweets with lower case
                      # are not serious in general ;)
                      text[0].isupper(),
                      # Skip questions
                      text[-1] != '?',
                      not url_re.search(text),
                      len(text.split())>=8,
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
        lang = gram.similarity(self.engram)>=0.20

        return all((ascii, lang))

    @staticmethod
    def parse_args():
        """ Parse command line arguments """

        parser = argparse.ArgumentParser(description="Fortwitude - Fortune cookies from Twitter")
        parser.add_argument('-t',dest='timeline',default='public',help='Source timeline to use (default public)')
        parser.add_argument('-l',dest='live',default=False,action='store_true',help='Force to use twitter live (default uses cache if available)')
        parser.add_argument('-s',dest='sample',default=50,type=int,help='Size of twitter messages used to sample (default 50)')
        parser.add_argument('-v',dest='verbose',default=False,action='store_true',help='Be verbose')
        args = parser.parse_args()
        return args
        
    def build_stream(self):
        """ Build a stream of tweets for making fortune cookies """
        
        tweets = []

        self.message('Building stream of size',self.sample,'...')

        for tweet in takewhile(lambda x: len(tweets)<self.sample,
                               self.twitter.get_status(self.source_api[self.source])):
            try:
                tweet_text = tweet['text']
                user = tweet.get('user',{}).get('screen_name', '')
                if self.filter(tweet_text):
                    self.message('Tweet',len(tweets)+1,':',tweet_text)
                    tweets.append((tweet_text, user))
            except KeyError:
                pass

        self.inform("built content pool of size",self.sample)
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
        
    def fortune(self):
        """ Get a fortune cookie from twitter """

        self.inform("\nFortwitude is starting up...")
        self.inform("Using",self.source,"timeline as source timeline...")
        self.inform("Sampling",self.sample,"tweets for random pool....")
        
        # If live, turn on verbose mode
        source = (not self.live) and self.get_cache()
        self.inform('Rebuilding content pool from twitter stream....')
            
        if not source:
            self.inform("querying twitter and building content from timeline...")
            pm = FakeProgressMeter()
            pm.start()
            
            # Cache might not exist or expired
            source = self.build_stream()
            pm.stop()
            
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
        
if __name__ == "__main__":
    args = Fortwitude.parse_args()
    f = Fortwitude(**args.__dict__)
    f.fortune()
