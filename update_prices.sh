#!/bin/bash
#

MKPATH=/home/pi/mynotebooks/mill_klubben
echo "Changing to {$MKPATH}"
cd $MKPATH
echo "Download starting from virtual env..."
/home/pi/jupytervenv/bin/python3 dl_mill_klubben_prices.py
