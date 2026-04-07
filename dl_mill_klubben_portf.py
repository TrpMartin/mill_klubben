# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.17.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Get movements of the Millionaerklubben portfolios automatically each day
# - set up a trigger or warning when the depot changes on the website (which is likely delayed compared to Saxo bank user followers)

# +
import requests
import json
from io import StringIO ## now needed for pd.read_html and BeautifulSoup string conversion
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import datetime as dt
import numpy as np
from pathlib import Path

import utils
# -


IN_NOTEBOOK = utils.in_notebook()
GET_NEW_TRANSACTIONS = True
today = dt.datetime.today().date()
yesterday = (dt.datetime.today() - dt.timedelta(days=1)).date()

if GET_NEW_TRANSACTIONS:
    URL = 'https://www.home.saxo/da-dk/campaigns/millionaerklubben'
    soup = BeautifulSoup(requests.get(URL).content, "html.parser")
    
    # find correct table:
    ## this was not working between 2024 Feb7 to 15th !! 
    tbl = soup.find_all(class_ = "v2-show-sm inspiration-table")
    for i in range(0, len(tbl)):
        for tag in tbl[i].find_all('div', class_ = "instrument__description-name"): # delete the stock name
            tag.clear()
    investor = soup.find_all('h2', class_ = "highlight")
    #print("Investor:", investor)
    raw_df = pd.read_html(StringIO(str(tbl)), decimal=',', thousands='.') # list of all tables dfs
    
    pd.set_option('display.max_rows', 10)
    #print(raw_df[0])
    
    df = pd.DataFrame()
    for i in range(0, len(raw_df)):
        raw_df[i]['Investor'] = investor[i].get_text() # 
        df = pd.concat([df,raw_df[i]], axis=0)

    df = df.drop(labels='Unnamed: 3', axis=1) # the "Handel" button field
    df['Amount'] = df.Antal * df.Åbningspris
    
    ## clean up Instrument
    df['Currency'] = df['Instrument'].str[-3:] # make a new Currency column
    
    df["Instrument"]= [x.replace('. '+str(y), '' ) for x, y in df[['Instrument','Currency']].to_numpy()]
    
    df[['Instrument', 'Stockexchange']] = df.Instrument.str.split(':', expand=True)
    df.Stockexchange = df.Stockexchange.replace(' ', '', regex=True)
    
    pd.set_option('display.max_rows', 80)
    df = df.reset_index(drop=True)
    
    # fix naming errors on website to derive correct Yahoo ticker names from Instrument names
    df.loc[(df.Instrument == 'AKERBP'), 'Instrument'] = 'AKRBP'
    df.loc[(df.Instrument == 'ALKb'), 'Instrument'] = 'ALK_B'
    df.loc[(df.Instrument == 'BEL'), 'Instrument'] = 'BELCO'
    df.loc[(df.Instrument == 'ATOS'), 'Instrument'] = 'ATO'
    df.loc[(df.Instrument == 'NOVOb'), 'Instrument'] = 'NOVO_B'
    df.loc[(df.Instrument == 'NZYMb'), 'Instrument'] = 'NZYM_B'
    df.loc[(df.Instrument == 'MAERSKb'), 'Instrument'] = 'MAERSK_B'
    df = df.drop(df[df.Instrument == 'VOYG'].index).reset_index(drop=True) # Voyager got delisted
    
    df['Ticker'] = df.Instrument.values+df.Stockexchange.replace(utils.ex_dict, regex=True)
    df.Ticker = df.Ticker.replace('_','-', regex=True )


# ## Write new transaction table to file

if GET_NEW_TRANSACTIONS:
    df = df.reset_index(drop=True) # reset before file saving
    if IN_NOTEBOOK:
        base_path = Path("__file__").parent # use "__file__" when in python, but __file__ when in streamlit
    else:
        base_path = Path(__file__).parent # use "__file__" when in python, but __file__ when in streamlit
    file = './data/mill_klubben_portf-'+str(today)+'.csv'
    file_path = (base_path / file).resolve()
    
    df.to_csv(file_path, sep=';', encoding='utf-8')
    print('Millionærklubbens portfolio was saved to file.')


print("Website scraping finished!")


