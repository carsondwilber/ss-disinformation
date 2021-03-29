import sys
from nltk.tokenize import TweetTokenizer
import csv
import argparse
import configparser
import pandas as pd
import re
import numpy as np
import csv
import nltk
from nltk import word_tokenize, FreqDist
from nltk.corpus import stopwords
nltk.download
nltk.download('wordnet')
nltk.download('stopwords')
# reload(sys)
# sys.setdefaultencoding('utf-8')


''' TODO: create ContentFilter class with below functionality '''


def clean(file):
    # remove mentions
    file = re.sub(r'@[A-Za-z0-9]+', '', str(file))
    # remove hashtags
    file = re.sub(r'#', '', file)
    # remove RT and FAV
    file = re.sub(r'RT[\s]+', '', file)
    # remove URLs
    file = re.sub(r'https?:\/\/\S+|www.\.\S+', '', file)
    # remove punctuation
    file = re.sub(r'[^\w\s]', '', file)
    # lower case text
    file = str.lower(file)
    return file
# remove numbers, lemmatize, and remove stop words


def lem_stop(tweetText):
    lemmatizer = nltk.stem.WordNetLemmatizer()
    tokenizer = TweetTokenizer()
    no_num = ''.join(word for word in tweetText if not word.isdigit())
    lem = [(lemmatizer.lemmatize(word))
           for word in tokenizer.tokenize((no_num))]
    stop_words = set(stopwords.words('english'))
    return [word for word in lem if not word in stop_words]


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Preprocess Twitter text")
    parser.add_argument("input", type=str, help="File path containing content to preprocess.")  # noqa
    parser.add_argument("output", type=str, help="File path at which to output result.")  # noqa
    parser.add_argument("-l", "--lemma", action='store_true', help="Lemmatize clean text")  # noqa
    args = parser.parse_args()

    tweets = pd.read_csv(args.input, engine='python', encoding="utf-8")

    tweets['clean_sentence'] = tweets['tweet_text'].apply(clean)

    if args.lemma:
        tweets['clean_words'] = tweets['clean_sentence'].apply(lem_stop)

    tweets.to_csv(args.output)
