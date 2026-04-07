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

import pandas as pd
import re

ex_dict = {
    'xcse': '.CO',
    'xmil': '.MI', # eigentlich Milan
    'xmce': '.MC',
    'xosl': '.OL',
    'xome': '.ST',
    'xhel': '.HE',
    'xetr': '.DE',
    'xams': '.AS',
    'xpar': '.PA',
    'xnys': '',
    'xtse': '.TO',
    'xtsx': '',
    'xasx': '.AX',
    'xlon': '.L',
    'xnas': ''
          }


#detect which environment this runs in
def in_notebook():
    try:
        shell = get_ipython().__class__.__name__
        return(shell == 'ZMQInteractiveShell')
    except NameError:
        return(False)

def replace_b_suffix(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return(df.copy())

    df[column] = df[column].astype(str).apply(
        lambda x: re.sub(r'(\w+)b(?=$|\.)', r'\1-B', x)
    )

    if column == 'Instrument':
        df[column] = df[column].str.replace('-', '_', regex=False)

    return(df.copy())


def cleanup_tickers_names(df: pd.DataFrame) -> pd.DataFrame:
    """ fix naming errors on website """
    
    df = replace_b_suffix(df, 'Instrument').copy()
    df = replace_b_suffix(df, 'Ticker').copy()
    ## other naming errors to fix
    df.loc[(df.Instrument == 'AKERBP'), 'Instrument'] = 'AKRBP'
    df.loc[(df.Instrument == 'BEL'), 'Instrument'] = 'BELCO'
    df.loc[(df.Instrument == 'ATOS'), 'Instrument'] = 'ATO'
    df.loc[(df.Instrument == 'NOVO-B'), 'Instrument'] = 'NOVO_B'
    df.loc[(df.Instrument == 'NZYM-B'), 'Instrument'] = 'NZYM_B'
    df.loc[(df.Instrument == 'GOMX_TR'), 'Instrument'] = 'GOMX'
    df.loc[(df.Ticker == 'GOMX-TR.ST'), 'Ticker'] = 'GOMX.ST'
    df.loc[(df.Ticker == 'TEN-NEW'), 'Ticker'] = 'TEN'
    df.loc[(df.Instrument == 'TEN_NEW'), 'Instrument'] = 'TEN'
    df.loc[(df.Instrument == 'SZGG'), 'Instrument'] = 'SZG'
    df.loc[(df.Ticker == 'SZGG.DE'), 'Ticker'] = 'SZG.DE'
    df.loc[(df.Instrument == 'COLO_B'), 'Instrument'] = 'COLO' # note, with out _B
    ## Delisted must be removed it is just simpler this way
    delisted = ['VOYG', 'EURN', 'TEST', 'ALCC', 'LOCK-A017']
    df = df[~df.Instrument.isin(delisted)].dropna()
    ## remove all Instruments that made it in the df, but actually were not traded and Antal is therefore 0 (aktie bytte)
    df = df.loc[~( (df.Antal.isna()) | (df.Antal==0) ) ]
    # the price in Milan is the same as in Germany
    df.Instrument = df.Instrument.replace({'INRG':'IQQH'}) # cannot download data for iShares Clean energy from Milan

    return(df.sort_values('Date').reset_index(drop=True))

## ISIN checks for checktax dashboard
def validate_isin(isin):
    """
    Validates an ISIN code using format check and check digit verification.
    
    Args:
        isin: String to validate as ISIN
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isin:
        return(False, "ISIN cannot be empty")
    
    # Remove any whitespace
    isin = isin.strip().upper()
    
    # Check format: 2 letters + 9 alphanumeric + 1 digit
    if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin):
        return(False, "Invalid ISIN format. Expected: 2 letters + 9 alphanumeric + 1 digit (e.g., US0378331005)")
    
    # Verify check digit
    if not verify_check_digit(isin):
        return(False, "Invalid check digit")
    
    return(True, "Valid ISIN")


def verify_check_digit(isin):
    """
    Verifies the ISIN check digit using the Luhn algorithm (modulo 10).
    
    Args:
        isin: ISIN string (12 characters)
        
    Returns:
        bool: True if check digit is valid
    """
    # Separate the code and check digit
    code = isin[:-1]  # First 11 characters
    check_digit = int(isin[-1])  # Last character
    
    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric_string = ""
    for char in code:
        if char.isalpha():
            # A=65 in ASCII, so A=65-55=10, B=66-55=11, etc.
            numeric_string += str(ord(char) - 55)
        else:
            numeric_string += char
    
    # Apply Luhn algorithm: multiply every other digit by 2, starting from the right
    digits = [int(d) for d in numeric_string]
    total = 0
    
    # Start from the rightmost digit (least significant)
    for i in range(len(digits) - 1, -1, -1):
        digit = digits[i]
        # Multiply every other digit by 2 (odd positions from the right)
        if (len(digits) - 1 - i) % 2 == 0:
            digit *= 2
        # Add individual digits (if doubled digit is >= 10, add both digits)
        total += digit // 10 + digit % 10
    
    # Calculate the check digit (ten's complement of sum modulo 10)
    calculated_check = (10 - (total % 10)) % 10
    
    return(calculated_check == check_digit)
