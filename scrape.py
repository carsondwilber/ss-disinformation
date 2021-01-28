import json
import csv
import tweepy
import re
import argparse
import configparser


def collect_hashtags_tweets(api, hashtags, operator, debug):
    partial_query = (' %s ' % operator).join(['#%s' % hashtag for hashtag in hashtags])
    query = '(%s) -filter:retweets' % partial_query
    return [tweet for tweet in tweepy.Cursor(api.search, q=query, lang="en", tweet_mode='extended').items(10)]

def collect_users_tweets(api, usernames, operator, debug):
    partial_query = (' %s ' % operator).join(['from:%s' % username for username in usernames])
    query = '(%s) -filter:retweets' % partial_query
    return [tweet for tweet in tweepy.Cursor(api.search, q=query, lang="en", tweet_mode='extended').items(10)]


def initialize_api(consumer_key, consumer_secret, access_token, access_secret):
    # Connect to Twitter via OAuth
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    # Initialize Tweepy API
    api = tweepy.API(auth, wait_on_rate_limit=True)

    return api


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Collect data from Twitter using Tweepy library.")
    parser.add_argument("--users", default=None, type=str, help='Twitter handles for users to collect Tweets from.')
    parser.add_argument("--hashtags", default=None, type=str, help='Twitter hashtags in Tweets to collect.')
    parser.add_argument("--operator", default='OR', type=str, choices=['OR', 'AND'], help='Operator to use for joining multiple items.')
    parser.add_argument("--output", default=None, type=str, help='File path for where to save results.')
    parser.add_argument("--debug", action='store_true', help='Print debug information to console.')
    parser.add_argument("--key", default=None, type=str, help='Twitter authentication key.')
    parser.add_argument("--secret", default=None, type=str, help='Twitter authentication secret.')
    parser.add_argument("--token", default=None, type=str, help='Twitter API token.')
    parser.add_argument("--token-secret", default=None, type=str, help='Twitter API token secret.')
    args = parser.parse_args()

    if (args.users is None and args.hashtags is None) or (args.users is not None and args.hashtags is not None):
        raise Exception("Must specify either --users OR --hashtags.")
    if args.users is not None and args.operator == 'AND':
        raise Exception("Cannot specify --operator AND with --users.")

    config = configparser.ConfigParser()
    config.read("./config.ini")

    consumer_key = None
    consumer_secret = None

    if config.has_section("auth"):
        if config.has_option("auth", "key"):
            consumer_key = config["auth"]["key"]
        if config.has_option("auth", "secret"):
            consumer_secret = config["auth"]["secret"]

    if config.has_section("api"):
        if config.has_option("api", "token"):
            access_token = config["api"]["token"]
        if config.has_option("api", "secret"):
            access_secret = config["api"]["secret"]

    if args.key is not None:
        consumer_key = args.key
    if args.secret is not None:
        consumer_secret = args.secret
    if args.token is not None:
        access_token = args.token
    if args.token_secret is not None:
        access_secret = args.token_secret

    api = initialize_api(consumer_key, consumer_secret, access_token, access_secret)

    tweets = []

    if args.users is not None:
        tweets = collect_users_tweets(api, args.users.split(','), args.operator, args.debug)
    if args.hashtags is not None:
        tweets = collect_hashtags_tweets(api, args.hashtags.split(','), args.operator, args.debug)

    with open(args.output, 'w') as f:
        w = csv.writer(f)

        w.writerow(['timestamp', 'tweet_text', 'username', 'all_hashtags', 'followers_count', 'location'])

        for tweet in tweets:
            w.writerow([tweet.created_at, tweet.full_text.replace('\n',' ').encode('utf-8'), tweet.user.screen_name.encode('utf-8'), [e['text'] for e in tweet._json['entities']['hashtags']], tweet.user.followers_count, tweet.user.location.encode('utf-8')])