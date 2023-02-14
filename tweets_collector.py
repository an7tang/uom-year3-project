import os, re, json
import tweepy
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# ------------ Helper function for creating timestamp ------------
def current_timestamp():    # UTC time
    utcnow = datetime.utcnow()
    timestamp = f"{utcnow.strftime('%y')}{utcnow.month:02}{utcnow.day:02}-{utcnow.hour:02}{utcnow.minute:02}{utcnow.second:02}"
    return timestamp

def tweets_creation_timestamp():
    d = datetime.utcnow() - timedelta(days=1)    
    date = datetime(year=d.year, month=d.month, day=d.day, hour=0, minute=0, second=0)
    timestamp = f"{date.strftime('%y')}{date.month:02}{date.day:02}"
    return timestamp

def collection_start_time():
    d = datetime.utcnow() - timedelta(days=1)    
    start_time = datetime(year=d.year, month=d.month, day=d.day, hour=0, minute=0, second=0)
    return start_time

def collection_end_time():
    d = datetime.utcnow() - timedelta(days=1)
    end_time = datetime(year=d.year, month=d.month, day=d.day, hour=23, minute=59, second=59)
    return end_time


class TweetsCollector:

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    # bearer_token = "AAAAAAAAAAAAAAAAAAAAAM2LjQEAAAAAG0VMbyPz8jVLj56owR0TbqzQlbw%3DucmTHIiwzieGt6BFotBVVgp7MFIGVbAf7MhcnJkwgvHtdOxcwy"
    tweet_fields = ['created_at']
    # user_fields = ['verified']
    # place_fields = ['country']
    # expansions = ['author_id', 'geo.place_id']

    def __init__(self):
        self.client = tweepy.Client(self.bearer_token)

    def _anonymise_data(self, content: str) -> str:
        pattern_username = r"(?<![\w@!#$%&*])(@\w{1,15})\b"  # Match '@username'
        pattern_url = r"(?:https://|http://)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*"
        
        usernames = re.findall(pattern_username, content)
        for i, name in enumerate(usernames):
            alias = f'USERNAME_{(i+1):02}'
            content = re.sub(name, alias, content)
        
        urls = re.findall(pattern_url, content)
        for i, url in enumerate(urls):
            alias = f'URL_{(i+1):02}'
            content = re.sub(url, alias, content)
        
        return content

    def count_tweet(self, query):
        counts = self.client.get_recent_tweets_count(query=query, granularity='day')

        str_print = ''
        total_count = counts.meta['total_tweet_count']

        for count in counts.data:
            start_time = re.search('\d{4}-(\d{2}-\d{2})', count['start']).group(1)
            end_time = re.search('\d{4}-(\d{2}-\d{2})', count['end']).group(1)
            str_print += f"{start_time} => {end_time} :  {count['tweet_count']}\n"
        str_print = f"Average: {total_count/7:.0f}/day\nTotal : {total_count} in 7 days\n\n" + str_print
        print(str_print)

        return counts

    def search_tweets_pagination(self, query: str, num: int):
        tweets = tweepy.Paginator(
            self.client.search_recent_tweets, 
            query=query, 
            max_results=10, # system limit: 500
            tweet_fields=self.tweet_fields,
            start_time=collection_start_time(),
            end_time=collection_end_time(),
        ).flatten(limit=num)
        
        return tweets
    
    def convert_tweets_to_dataframe(self, tweets: tweepy.Response) -> pd.DataFrame:
        tweets_list = []
        # with pagination: for tweet in tweets
        # without pagination: for tweet in tweets.data
        for tweet in tweets:
            set_tweet_data= {
                'created_at': tweet.created_at,
                'text': self._anonymise_data(tweet.text)
            }
            tweets_list.append(set_tweet_data)
        
        df = pd.DataFrame(tweets_list)
        return df

    def convert_tweets_to_list_of_dict(self, tweets: tweepy.Response) -> list:
        tweets_list = []
        # with pagination: for tweet in tweets
        # without pagination: for tweet in tweets.data
        for tweet in tweets:
            tweet_dict = {
                "creation_date": tweet.data["created_at"],
                "content": self._anonymise_data(tweet.data["text"])
            }
            tweets_list.append(tweet_dict)

        # tweets_json = json.dumps(tweets_list, indent=2)
        return tweets_list


if __name__ == '__main__':

    # -------------- (Search / Count) Query --------------
    collector = TweetsCollector()
    query = "(covid OR covid-19 OR coronavirus) -is:retweet lang:en"
    # tweet_counts = collector.count_tweet(query)
    tweets = collector.search_tweets_pagination(query, num=50)  
    # ----------------------------------------------------


    # ----------------- Convert & Store ------------------
    # df = collector.convert_tweets_to_dataframe(tweets)  # Convert to DataFrame
    tweets_list = collector.convert_tweets_to_list_of_dict(tweets)  # Convert to JSON
    
    path = './dataset/raw/'      # for Mac
    # path = '/home/p11333at/nlp-project/dataset/'      # for DS Server  
    filename = f"tweets_{tweets_creation_timestamp()}_#{len(tweets_list)}_({current_timestamp()}).json"

    with open(f"{path}{filename}", "w") as f:
        json.dump(tweets_list, f, indent=2)
    # df.to_csv(f"{path}{filename}", encoding='utf-8', index=False)

    if os.path.exists(f"{path}{filename}"):
        print(f"The file '{filename}' is created.")
    # ----------------------------------------------------


    # ----------------- Record Metadata ------------------
    counts = collector.client.get_recent_tweets_count(query=query, granularity='day')

    yesterday_date = str(collection_start_time().date())
    counts_of_yesterday = 0
    for data in counts.data:
        if yesterday_date in data["start"]:
            counts_of_yesterday = data["tweet_count"]

    dict_counts = {yesterday_date: counts_of_yesterday}

    filename_meta = "meta.json"


    if os.path.exists(f"{path}{filename_meta}"):
        with open(f"{path}{filename_meta}", "r+") as f:
            meta = json.load(f)
            meta.update(dict_counts)
            f.seek(0)
            json.dump(meta, f, indent=2)
            # f.write(json.dumps(meta, indent=2))
            f.truncate()
    else:
        with open(f"{path}{filename_meta}", "x") as f:
            json.dump(dict_counts, f, indent=2)

    print(f"The tweet counts is recorded in '{filename_meta}' file.")
    # ----------------------------------------------------

    print("Successful!")

    
