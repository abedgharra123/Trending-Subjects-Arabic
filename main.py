from numpy import character
from pytz import HOUR
import tweepy
import arabic_reshaper
import requests # For sending GET requests from the API
import os # For saving access tokens and for file management when creating and adding to the dataset
import json # For dealing with json responses we receive from the API
import pandas as pd # For displaying the data after
import csv # For saving the response data in CSV format
import datetime # For parsing the dates received from twitter in readable formats
import dateutil.parser
import unicodedata
import time #To add wait time between requests
import matplotlib.pyplot as plt
import random

from trace import CoverageResults
from tweepy import Stream
from bidi.algorithm import get_display

# -------------------------------------------- WORKING WITH TWITTER API -------------------------------------------

def auth():
    return os.getenv('TOKEN')

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

def create_url(keyword, start_date, end_date, max_results = 10):
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    #change params based on the endpoint you are using
    query_params = {
        'query': keyword,
        'start_time':start_date,
        'max_results':max_results
    }
    return (search_url, query_params)

def connect_to_endpoint(url, headers, params): # gets the request from google
   #params object received from create_url function
    print("***********************************")
    print(url)
    print(params)
    print("***********************************")
    response = requests.request("GET", url, headers = headers, params = params)
    print("Endpoint Response Code: " + str(response.status_code)+"\n\n")
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def ConvertToDFAndSaveCSV(json_response):
    dataframe = pd.DataFrame(json_response['data'])
    dataframe['text'] = dataframe['text'].apply(lambda txt: txt.replace("\n"," "))

    df = dataframe
    df['text'] = dataframe['text'].apply(lambda txt: u','+arabic_reshaper.reshape(txt))
    df.to_csv(r'tweets.csv', mode='a', sep='\t', encoding='utf-8-sig') 

    dataframe['text'] = dataframe['text'].apply(lambda txt: arabic_reshaper.reshape(txt))
    dataframe['text'] = dataframe['text'].apply(lambda txt: get_display_Exeption_Handler(txt))
    print(f'{dataframe} \n \n')
    return dataframe

def get_display_Exeption_Handler(txt):
    try:
        txt = get_display(txt)
    except:
        txt = txt
    return txt

def InvokeRequest(keyword,start_time,max_results):
    bearer_token = auth()
    headers      = create_headers(bearer_token)
    end_time     = "2022-05-17T00:00:00Z"

    url = create_url(keyword, start_time,end_time, max_results)
    json_response = connect_to_endpoint(url[0], headers, url[1])
    df = ConvertToDFAndSaveCSV(json_response)
    return df

# 100 search resul from keyword : السعودية 
# dataframe = InvokeRequest("السعودية#",100,True)
def GetPostsAsDataframe(ammount):
    start_time = f"2022-05-{random.randint(18, 23)}T{str(random.randint(0, 23)).zfill(2)}:{str(random.randint(0, 59)).zfill(2)}:{str(random.randint(0, 59)).zfill(2)}Z"
    print(start_time)
    dataframe = InvokeRequest("السعودية#",start_time,100)
    for i in range(ammount-1):
        start_time = f"2022-05-{random.randint(18, 23)}T{str(random.randint(0, 23)).zfill(2)}:{str(random.randint(0, 59)).zfill(2)}:{str(random.randint(0, 59)).zfill(2)}Z"
        print(start_time)
        dataframe = pd.concat([dataframe,InvokeRequest("السعودية#",start_time,100)])
    return dataframe
# -------------------------------------------- ANALYZING DATA -------------------------------------------

import nltk
import re
import string

from nltk.tokenize import word_tokenize
from collections import Counter
from nltk.corpus import stopwords
nltk.download('stopwords')

def GetAllTextFromDataFramePosts(dataframe):
    all_text = dataframe['text'].values.tolist()
    words_list = list(map(lambda x:x.split(' '),all_text))
    words_list = [item for sublist in words_list for item in sublist]
    return words_list

def GetAndPrintTrendingWords(words_list,numberOfWords):
    c = Counter(words_list)
    common = c.most_common(numberOfWords)
    print(f'{common}\n\n')
    return common

def GetFilteredArabicWords(words_list):
    arb_stopwords = set(stopwords.words("arabic"))
    arb_stopwords = set(map(lambda txt: arabic_reshaper.reshape(txt),arb_stopwords))
    arb_stopwords = set(map(lambda txt: get_display(txt),arb_stopwords))
    stop_words_set = set(stopwords.words("english"))
    Characters     = list(string.printable)

    words_list = [w for w in words_list if w not in arb_stopwords]
    words_list = [w for w in words_list if w not in stop_words_set]
    words_list = [w for w in words_list if w not in Characters]
    words_list = [w for w in words_list if w not in ['RT','','،',',RT','..']]
    return words_list


dataframe = GetPostsAsDataframe(10) # hundreds
words_list = GetAllTextFromDataFramePosts(dataframe)

print('\n\nBefore removing stopwords')
GetAndPrintTrendingWords(words_list,20)

print('\n\nAfter removing stopwords')
filtered_words_list = GetFilteredArabicWords(words_list)
common = GetAndPrintTrendingWords(filtered_words_list,20)



df = pd.DataFrame(common, columns =['Keyword', 'Appeared'])
print(df)
series = pd.Series(list(df['Appeared']), list(df['Keyword']), name="series")
print(series)
series.plot.pie(figsize=(10, 10))
plt.show(block=True)