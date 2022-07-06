from textblob import TextBlob
import tweepy
import pandas as pd
import os
import collections

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def twitter_worker(ticker):
    d = collections.deque(maxlen = 144)

    # Authentication
    consumerKey = os.environ['CONSUMERKEY']
    consumerSecret = os.environ['CONSUMERSECRET']
    accessToken = os.environ['ACCESSTOKEN']
    accessTokenSecret = os.environ['ACCESSTOKENSECRET']

    client = tweepy.Client(bearer_token=os.environ['BEARERTOKEN'],
                        consumer_key=consumerKey,
                        consumer_secret=consumerSecret,
                        access_token=accessToken,
                        access_token_secret=accessTokenSecret)

    #Sentiment Analysis
    def percentage(part,whole):
        return 100 * float(part)/float(whole)

    tweets = client.search_recent_tweets(query=ticker, max_results = 25)

    positive = 0
    negative = 0
    neutral = 0
    polarity = 0
    tweet_list = []
    neutral_list = []
    negative_list = []
    positive_list = []

    for tweet in tweets.data:
        tweet_list.append(tweet.text)
        analysis = TextBlob(tweet.text)
        score = SentimentIntensityAnalyzer().polarity_scores(tweet.text)
        neg = score["neg"]
        neu = score["neu"]
        pos = score["pos"]
        comp = score["compound"]
        polarity += analysis.sentiment.polarity

        if neg > pos:
            negative_list.append(tweet.text)
            negative += 1

        elif pos > neg:
            positive_list.append(tweet.text)
            positive += 1

        elif pos == neg:
            neutral_list.append(tweet.text)
            neutral += 1

        positive = percentage(positive, 100)
        negative = percentage(negative, 100)
        neutral = percentage(neutral, 100)
        polarity = percentage(polarity, 100)

    tweet_list = pd.DataFrame(tweet_list)
    positive_list = pd.DataFrame(positive_list)
    d.append(len(positive_list)/len(tweet_list))

    def count_and_sum(iter):
        count = sum = 0
        for item in iter:
            count += 1
            sum += item
        return count, sum

    count, sum = count_and_sum(d)

    return (sum/count)