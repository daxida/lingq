import os
import requests
import json
import sys
import pandas as pd
import datetime
from dotenv import dotenv_values

# Assumes that .env is on the root
parent_dir = os.path.dirname(os.getcwd())
env_path = os.path.join(parent_dir, '.env')
config = dotenv_values(env_path)

KEY = config["APIKEY"]
headers = {'Authorization': f"Token {KEY}"}
params = {'interval': 'today'}

current_day = datetime.datetime.today().strftime('%A')


def printJSON(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def main():
    res = requests.get(
        'https://www.lingq.com/api/v2/ja/progress/',
        params=params,
        headers=headers
    ).json()

    del res["intervals"]

    df = pd.DataFrame([res])
    df = df.transpose()
    df = df.reset_index()
    df.columns = ['Attribute', current_day]

    if os.path.exists('stats.xlsx'):
        print('Previous stats.xlsx found, appending:')

        prev_df = pd.read_excel('stats.xlsx')
        df = pd.concat([prev_df, df[current_day]], axis=1)
    else:
        print('Could not find stats.xlsx, creating:')
        

    with pd.ExcelWriter('stats.xlsx') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)

    # print(df)

    print("Finished!")


main()
