import sys
import tweepy
import hashlib
import secret
from celery import Celery

API_KEY = secret.API_KEY
API_SECRET = secret.API_SECRET
ACCESS_TOKEN = secret.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = secret.ACCESS_TOKEN_SECRET

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True)
if not api:
    print("Can't Authenticate")
    sys.exit(-1)


def fetch_tweets(searchQuery, celery, num_tweets=1000):
    # API CONSTANTS
    # searchQuery = '#CaliforniaFires'  # this is what we're searching for
    # maxTweets = 100  # Some arbitrary large number
    tweetsPerQry = 100  # this is the max the API permits
    fName = 'tweets.txt'  # We'll store the tweets in a text file.
    #
    # # If results from a specific ID onwards are reqd, set since_id to that ID.
    # # else default to no lower limit, go as far back as API allows
    sinceId = None
    #
    # # If results only below a specific ID are, set max_id to that ID.
    # # else default to no upper limit, start from the most recent tweet matching the search query.
    max_id = -1
    #
    tweetCount = 0
    completed_lines_hash = set()
    #
    print("Downloading max {0} tweets".format(num_tweets))
    with open(fName, 'wb') as f:
        while tweetCount < num_tweets:
            try:
                if max_id <= 0:
                    if not sinceId:
                        new_tweets = api.search(q=searchQuery, count=tweetsPerQry)
                    else:
                        new_tweets = api.search(q=searchQuery, count=tweetsPerQry,
                                                since_id=sinceId)
                else:
                    if not sinceId:
                        new_tweets = api.search(q=searchQuery, count=tweetsPerQry,
                                                max_id=str(max_id - 1))
                    else:
                        new_tweets = api.search(q=searchQuery, count=tweetsPerQry,
                                                max_id=str(max_id - 1),
                                                since_id=sinceId)
                if not new_tweets:
                    print("No more tweets found")
                    break
                for tweet in new_tweets:
                    # hashValue = hashlib.md5(tweet.text.rstrip().encode('utf-8')).hexdigest()
                    # if hashValue not in completed_lines_hash:
                    f.write(tweet.text.encode("utf-8"))
                    # completed_lines_hash.add(hashValue)
                tweetCount += len(new_tweets)
                celery.update_state(state='PROGRESS',
                              meta={'current': tweetCount, 'total': num_tweets,
                                    'status': 'Downloading...'})
                print("Downloaded {0} tweets".format(tweetCount))
                max_id = new_tweets[-1].id
            except tweepy.TweepError as e:
                # Just exit if any error
                print("some error : " + str(e))
                break

    print("Downloaded {0} tweets, Saved to {1}".format(tweetCount, fName))
    return {'current': tweetCount, 'total': num_tweets, 'status': 'Task completed!'}
