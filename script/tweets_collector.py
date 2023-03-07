import os, re, json, time
import tweepy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()


# ------------ Helper function for timestamp ------------
def today(backward_days: int):
    d = datetime.utcnow() - timedelta(days=backward_days)
    date = datetime(year=d.year, month=d.month, day=d.day, hour=0, minute=0, second=0)
    return date

def file_timestamp(datetime):
    return f"{datetime.strftime('%y')}{datetime.month:02}{datetime.day:02}"


# ------------ Class TweetsCollector ------------
class TweetsCollector:

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    tweet_fields = ['created_at']

    def __init__(self):
        self.client = tweepy.Client(self.bearer_token, wait_on_rate_limit=True)

    def _anonymise_data(self, content: str) -> str:
        # pattern_username = r"(?<![\w@!#$%&*])(@\w{1,15})\b"  # Match '@username'
        # pattern_url = r"(?:https://|http://)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9\(\)]{1,6}\b[-a-zA-Z0-9\(\)@:%_\+.~#?&//=]*"
        
        # usernames = re.findall(pattern_username, content)
        # for i, name in enumerate(usernames):
        #     alias = f'USERNAME_{(i+1):02}'
        #     content = re.sub(name, alias, content)
        
        # urls = re.findall(pattern_url, content)
        # for i, url in enumerate(urls):
        #     alias = f'URL_{(i+1):02}'
        #     content = re.sub(url, alias, content)
        
        # return content
        ...
    
    def anonymise_tweets_list(self, tweets_list: str) -> str:
        pattern_username = r"(?<![\w@!#$%&*])(@\w{1,15})\b"  # Match '@username'
        pattern_url = r"(?:https://|http://)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9]{1,6}\b[-a-zA-Z0-9@:%_\+.~#?&//=]*"

        new_list = []
        for index, tweet in enumerate(tweets_list):
            content = tweet['content']
            usernames = re.findall(pattern_username, content)
            
            # print(f"{index}: {content}", end="\r")
            try:
                for i, name in enumerate(usernames):
                    alias = f'USERNAME_{(i+1):02}'
                    content = re.sub(name, alias, content)
                
                urls = re.findall(pattern_url, content)
                for i, url in enumerate(urls):
                    alias = f'URL_{(i+1):02}'
                    content = re.sub(url, alias, content)
            except Exception as e:
                print(f"Error occurs in: index [{index}] :\n{content}", end="\r")
                raise


            new_tweet = {
                "creation_date": tweet["creation_date"],
                "content": content
            }

            new_list.append(new_tweet)
        
        return new_list

    def count_tweet(self, query, mute=False):
        counts = self.client.get_recent_tweets_count(query=query, granularity='day')

        if mute:
            return counts

        str_print = ''
        total_count = counts.meta['total_tweet_count']

        for count in counts.data:
            start_time = re.search('\d{4}-(\d{2}-\d{2})', count['start']).group(1)
            end_time = re.search('\d{4}-(\d{2}-\d{2})', count['end']).group(1)
            str_print += f"{start_time} => {end_time} :  {count['tweet_count']}\n"
        str_print = f"Average: {total_count/7:.0f}/day\nTotal : {total_count} in 7 days\n\n" + str_print
        print(str_print)

        return counts

    def limit_handler(self, paginator):
        while True:
            try:
                yield next(paginator)
            except tweepy.errors.TooManyRequests:
                print('\nReached rate limite. Sleeping for >15 minutes')
                time.sleep(15 * 61)
            except StopIteration:
                break

    def search_tweets_pagination(self, query: str, num: int, start_date, end_date):
        tweets = self.limit_handler(
            tweepy.Paginator(
                self.client.search_recent_tweets, 
                query=query, 
                max_results=100, # max limit: 100
                tweet_fields=self.tweet_fields,
                start_time=start_date,
                end_time=end_date,
            ).flatten(limit=num)
        )
        
        return tweets
    
    def convert_tweets_to_dataframe(self, tweets: tweepy.Response) -> pd.DataFrame:
    #     tweets_list = []
    #     # with pagination: for tweet in tweets
    #     # without pagination: for tweet in tweets.data
    #     for tweet in tweets:
    #         set_tweet_data= {
    #             'created_at': tweet.created_at,
    #             'text': self._anonymise_data(tweet.text)
    #         }
    #         tweets_list.append(set_tweet_data)
        
    #     df = pd.DataFrame(tweets_list)
    #     return df
        ...


    def convert_tweets_to_list_of_dict(self, tweets: tweepy.Response) -> list:
        tweets_list = []
        # with pagination:     for tweet in tweets
        # without pagination:  for tweet in tweets.data
        for i, tweet in enumerate(tweets):
            tweet_dict = {
                "creation_date": tweet.data["created_at"],
                "content": tweet.data["text"]
            }
            tweets_list.append(tweet_dict)
            print(f'Current number: {i+1}', end='\r')
        print('\n\033[32mConvertion successfully finished!\033[0m')
        # tweets_json = json.dumps(tweets_list, indent=2)
        return tweets_list


if __name__ == '__main__':
    # -------------- Initilisation --------------
    collector = TweetsCollector()

    backward_days = 1   # Set to 1 to collect yesterday's (Max: 6)
    collection_date = today(backward_days)
    start_time = collection_date
    end_time = today(backward_days) + timedelta(days=1)

    query = "(covid OR covid19 OR covid-19 OR coronavirus OR (corona virus) OR pandemic) -is:retweet lang:en"


    # -------------- Count tweets --------------
    counts_in_hour = collector.client.get_recent_tweets_count(query=query, granularity='hour', start_time=start_time, end_time=end_time)

    counts = []
    for data in reversed(counts_in_hour.data):
        start = data['start']
        end = (datetime.strptime(data['end'], '%Y-%m-%dT%H:%M:%S.000Z') - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        counts.append({
            "end": end,
            "start": start,
            "tweet_count": data['tweet_count']
        })

    expected_num = np.sum([hour['tweet_count'] // 2 for hour in counts])


    # -------------- Collect tweets --------------
    tweets_list = []
    for hour in counts:
        start = hour['start']
        end = hour['end']
        num = hour['tweet_count'] // 2  # Get 50%
        print(f"----- {start} -----")
        generator = collector.search_tweets_pagination(query, num, start, end)
        tweets = collector.convert_tweets_to_list_of_dict(generator)
        tweets_list.extend(tweets)


    # -------------- Anonymise tweets --------------
    anonymous_tweets_list = collector.anonymise_tweets_list(tweets_list)


    # -------------- Store results --------------
    path = "/home/p11333at/nlp-project/data/raw/"
    filename = f"tweets_{file_timestamp(start_time)}_#{len(tweets_list)}.json"

    with open(f"{path}{filename}", "w") as f:
        for line in anonymous_tweets_list:
            json.dump(line, f)
            f.write('\n')

    if os.path.exists(f"{path}{filename}"):
        print(f"The file '{filename}' is created.")