fortwitude - Fortune cookies with Twitter
========================================

Fortwitude is a program which tries to make sense out of
the global twitter stream by sampling them for fortune
"cookies".

The program simulates the Unix utility __fortune__ with
source as the public or home timeline of the user.

REQUIREMENTS
------------
The program needs the PTT (python-twitter-tools) library
which is automatically installed by setup.py.

If it fails to install because of some error, you can get it from 
https://pypi.python.org/packages/source/t/twitter/twitter-1.10.0.tar.gz .

INSTALL
-------

```bash
$ sudo python setup.py install

```

The program installs the same script in two names
 - ___fortwitude___ and ___fortitude___ .

RUNNING
-------

The first time you run, fortwitude requests for OAuth 
authentication for your twitter account. The authentication
is done entirely on the command line.

It also builds an initial pool of __reasonable__ tweets which
are saved to a file in the home folder. The initial sample
size is 50. 

The program has an inbuilt detector for English
language tweets and a basic profanity filter to filter out
profane tweets. The curated content is saved and used as 
the pool for producing __cookies__.

SAMPLE USAGE
------------

```bash
$ fortitude 


Fortwitude is starting up...
Using public timeline as source timeline...
Sampling 50 tweets for random pool....
Rebuilding content pool from twitter stream....
querying twitter and building content from timeline...
............................built content pool of size 50
built content.
writing cache.
No loyalty these days , one offer and your thoughts change - Suffy_M
```

Once the pool is built just tying ___fortitude___ or ___fortwitude___
on the console produces a random __fortune cookie__.

```bash

$ fortitude

There is nothing so fatal to character as half-finished tasks. - ParentClub80998

$ fortitude

Realized it's the 10th.. marking one month from today I will have lived 24 years. What a depressing birthday! Almost halfway to 50.. - TooCoolJess

$ fortitude 
Broke my phone the week before iOS 7 :( - Heart_Smart69

```

__NOTE__: It takes a while to build the initial pool as a lot
of content needs to be filtered. You need to be patient :) 

REFRESHING CONTENT
------------------
The local cache has a TTL of 24 hours after which it is automatically
refreshed and new tweets are fetched. To force fetch live tweets use
the -l option.

OTHER OPTIONS
-------------
You can pass __home__ to the -t option to use your home timeline
instead of the public timeline. 

Complete command-line options are below.

```bash
anand@home-laptop$ fortitude -h
usage: fortitude [-h] [-t TIMELINE] [-l] [-s SAMPLE] [-v]

Fortwitude - Fortune cookies from Twitter

optional arguments:
  -h, --help   show this help message and exit
  -t TIMELINE  Source timeline to use (default public)
  -l           Force to use twitter live (default uses cache if available)
  -s SAMPLE    Size of twitter messages used to sample (default 50)
  -v           Be verbose
 
```

BUGS, SUGGESTIONS
-----------------
@pythonhacker 










