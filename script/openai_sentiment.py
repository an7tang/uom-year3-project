import os, json
from dotenv import load_dotenv
import openai

# class OpenAISentiment():
class OpenAISentiment():

    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    model_davinci = "text-davinci-003"  # Best model
    model_curie = "text-curie-001"  # Second-best, but faster

    # def __init__(self, dataset_path):
        # self.dataset_path = dataset_path
        # load_dotenv()
        # openai.api_key = os.getenv("OPENAI_API_KEY")

    def _insert_tweets(self, tweets_list):
        result = ""
        for i, tweet in enumerate(tweets_list):
            result += f"{i+1}.\n{tweet}\n"
        
        return result
    
    def get_sentiments_in_json(self, tweets_list):
        prompt = f'''Classify the sentiment in these tweets, using 0, 1, 2 to represent positive, neutral and negative respectively. The result must be json format with curly brackets, and property name must be the given index number enclosed in double quotes.\n\n{self._insert_tweets(tweets_list)}\n\nThe result should be json format.'''

        response = openai.Completion.create(
            model=self.model_davinci,
            prompt=prompt,
            temperature=0,
            max_tokens=500
            )
        
        # results = json.loads(response["choices"][0]["text"])
        # return results

        return response["choices"][0]["text"]