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

# # Get stock prices of Millionaerklubben portfolios
# - this script is now executed from cronjob via a shell wrapper! 
# - dowload price data with Yahooquery and update the SQL

# +
from pathlib import Path
import dateutil.parser as dparser
import pandas as pd
from time import sleep
import datetime as dt
import numpy as np
from mystocks import retrievals, definitions, conversions

import utils
# -

START_DL_DATE = dt.datetime(2024,12,31)

# +

## modern way is to use pathlib instead of "import os" and string path
BASE_PATH = Path(__file__).resolve().parent
DATA_PATH = BASE_PATH / "data"

DB_PATH = DATA_PATH / 'MK_PRICES.db'

csv_files = list(DATA_PATH.glob("*.csv"))


today = dt.date.today()
yesterday = (today - dt.timedelta(days=1))
#round to decimals in pandas tables output
pd.options.display.float_format = '{:,.2f}'.format

# +
csv_files = list(Path(DATA_PATH).glob("*.csv"))
frames = []

for f in csv_files:
    x = pd.read_csv(f, sep=';', index_col=0)
    extracted_date = dparser.parse(f.name, fuzzy=True)
    x['Date'] = extracted_date
    frames.append(x)

df = pd.concat(frames, axis=0)
# -

## cleanup
df = utils.cleanup_tickers_names(df)

# +
#df.loc[df.Instrument.str.startswith('COL')]
# -

# ## limit to date

df = df.loc[df.Date > START_DL_DATE]
print("Downloading Tickers from start date", START_DL_DATE.strftime('%Y-%m-%d'))

# make a new dataframe 'dl' which contains only the unique tickers for stock price downloading
dl = df[['Instrument', 'Ticker']].copy().drop_duplicates().reset_index(drop=True)

# +
## uncomment for test and download only last three
#dl = dl[-3:].reset_index(drop=True) #

for i in range(0,len(dl)):
    res = retrievals.yq_historical_prices_importer(dl.loc[i,'Ticker'], 
                                                   dl.loc[i,'Instrument'], 
                                                   db_path=DB_PATH)
# -

print("")
print("#"*50)
print("MK stock prices download finished!")


