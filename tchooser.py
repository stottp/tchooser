#!/usr/bin/env python

from __future__ import division
from secrets import *
from twitter import *
import random
import re
import string
import time
import urllib2


def authorise_twitter():
    '''Authorise access to Twitter'''
    return Twitter(auth=OAuth(token = token, 
                                token_secret = token_secret, 
                                consumer_key = consumer_key, 
                                consumer_secret = consumer_secret),
                                retry=True)  


def check_correct_hashtag(tweet):
    '''Checks the correct hashtag has been used to start the round'''
    return True if re.search(r'(^|\W)#whoshouldmakethedrinks($|\W)', tweet, flags=re.IGNORECASE) else False  
      

def extract_players(tweet, caller):
    '''Takes a request and extracts unique players twitter handles excluding @tchooser and the caller of RG'''
    return list(set([word.lower() for word in tweet.split() if word.startswith('@') and not word == '@tchooser' and not word == caller]))
    
    
def get_tweet_information(tweet, caller):
    '''Returns a tuple of the tweet information and players from tweet'''
    return (tweet, extract_players(tweet, caller))
    
    
def caller_check(caller, players):
    '''Checks if originator handle is in the list becuase currenty returns the results as unicode'''
    for player in players:
        if re.search(caller, player, flags=re.IGNORECASE):
            return True
    
    
def tea_maker(players):
    '''Chooses a random twitter handle from the list'''
    return random.choice(players)
    
    
def check_character_length(tweet):
    '''Checks the character length and if less than 240 characters it returns the tweet'''
    if len(tweet) <= 240:
        return tweet #Need to think of a better way of handling if a tweet is over 240 characters
    
        
def get_current_epoch_time():
    '''Get the current epoch time'''
    return int(time.time())

    
def get_current_limit_ratings(t):
    '''Calculates how much sleep time is required depending on current rating limit '''
    try:
        limits = t.application.rate_limit_status()['resources']['statuses']['/statuses/mentions_timeline']
        print limits['remaining'], (limits['reset'] - get_current_epoch_time()) / limits['remaining']
        return (limits['reset'] - get_current_epoch_time()) / limits['remaining']  
    except ZeroDivisionError:
        return 12 
        
                         
def get_last_tweet_id(t):
    '''Queries twitter to get the last tweet id to prevent duplicate tweets sent on startup or if bot turned off'''
    return t.statuses.mentions_timeline()[0]['id_str']
    
    
def prepare_tweet(caller, players, num_of_players):
    if num_of_players < 1:
        return '{} you have to make the drinks but you know that becuase you called the RG on your own!?! - {}'.format(caller, make_salt())
    else:
        chosen_one = tea_maker(players)
        print players, chosen_one
        if caller in players: 
            players.remove(caller)
        return '{} has called the RG including {}. {} has been selected to make the brew!!! - {}'.format(caller, ' & '.join([', '.join(players[:-1]), 
                    players[-1]] if len(players) > 2 else players).encode('utf-8').strip(), chosen_one, make_salt())
                    
                    
def make_salt():
    ''' Produces 5 random characters to make tweet unique'''
    return ''.join(random.choice(string.letters) for n in xrange(5))
    
            
def get_tweets():
    tweet_id = '' # need to query_the_database to get it if null and then can bring this further down.
    while True:
        try:
            t = authorise_twitter()
            if not tweet_id:
                tweet_id = get_last_tweet_id(t)
            time.sleep(get_current_limit_ratings(t))
            print 'waiting for tweet...'
            mentions = t.statuses.mentions_timeline(since_id = tweet_id)
            for mention in reversed(mentions): #reverse to read oldest tweet first
                players = [] #reset list
                if check_correct_hashtag(mention['text']) and not mention['retweeted']: #Checks correct # & tweet not retweeted
                    print 'processing tweet {}'.format(mention['text'])
                    caller = '@' + mention['user']['screen_name']
                    tweet, players = get_tweet_information(tweet = mention['text'], caller = caller)
                    if caller_check:
                        players.append(caller)
                    print 'players are {}'.format(players).encode('utf-8').strip()
                    draft_tweet = prepare_tweet(caller = caller, players = players, num_of_players = len(players))
                    print draft_tweet
                    t.statuses.update(status = draft_tweet)
                    tweet_id = mention['id_str']
        except TwitterError as e:
            print e
        except urllib2.URLError, e:
            print e.args
            time.sleep(10)
        except KeyboardInterrupt:
            break
    
    
            
def test():
    #Test the correct hashtag has been used
    assert check_correct_hashtag('@tchooser @stottp @handletest @test1 @test2 #WhoShouldMakeTheDrinks') == True
    assert check_correct_hashtag('@tchooser @stottp @handletest @test1 @test2 #WhoShouldMakeTheDrinksTest') == False
    assert check_correct_hashtag('@stottp #whoshouldmakethedrinks something else') == True
    assert check_correct_hashtag('#whoshouldmakethedrinks something else @stottp') == True
    assert check_correct_hashtag('@stottp #whoshouldmakethedrinks') == True
    assert check_correct_hashtag('@stottp #WhoShouldMakeTheDrinks something else') == True
    assert check_correct_hashtag('@stottp #whoshouldmakethedrinkss something else') == False
    assert check_correct_hashtag('@stottp #whoshouldmakethedrinksSomethingSfter something else') == False
    assert check_correct_hashtag('@stottp SomethingBefore#whoshouldmakethedrinks something else') == False
    assert extract_players('@handletest @tswticher @tswticher @Tswticher @stottp #WhoShouldMakeTheDrinks #Test #Test', '@tswticher') == [u'@tswticher', u'@stottp']
    assert extract_players('@handletest No handles included', '@tswticher') == []
    assert extract_players('No handles at all included', '@tswticher') == []
    #Test the correct players have been selected
    print 'tests passed'
    

if __name__ == '__main__':
    get_tweets()
    
    

#Items to improve
#1.Hook it up to the datastore 
#2.print len(mention['entities']['user_mentions']) # print the number of user mentions. Maybe check count = players


    
    