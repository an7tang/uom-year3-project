from tweets_collector import *
import re
import os
import json

# Collect tweets count for recent 7 days
collector = TweetsCollector()
query = "(covid OR covid19 OR covid-19 OR coronavirus OR (corona virus) OR pandemic) -is:retweet lang:en"
day_counts = collector.client.get_recent_tweets_count(query=query, granularity='day')


# Store results in dict
output = {}
for i, day in enumerate(day_counts.data):
    if i == 0 or i == len(day_counts.data)-1:
        continue
    date = re.search(r"\d{4}-\d{2}-\d{2}", day["start"]).group(0)
    count = day["tweet_count"]
    output.update(
        {date : 
            {"total" : count,
             "hourly" : {}}
        }
    )


start_time = today(6)
end_time = today(1) + timedelta(days=1)

hour_counts = collector.client.get_recent_tweets_count(query=query, granularity='hour', start_time=start_time, end_time=end_time)


for hour in hour_counts.data:
    start = hour["start"]
    date = re.search(r"\d{4}-\d{2}-\d{2}", start).group(0)
    time = re.search(r"\d{2}:\d{2}:\d{2}", start).group(0)
    output[date]["hourly"].update({time : hour["tweet_count"]})


# Output results to file
filename_meta = "meta.json"
path = "/home/p11333at/nlp-project/data/"

if os.path.exists(f"{path}{filename_meta}"):
    with open(f"{path}{filename_meta}", "r+") as f:
        # Load and update
        meta = json.load(f)
        meta.update(output)
        # Overwrite
        f.seek(0)
        json.dump(meta, f, indent=2)
        f.truncate()
else:
    with open(f"{path}{filename_meta}", "x") as f:
        json.dump(output, f, indent=2)

print(f"The tweet counts is recorded in '{filename_meta}' file.")