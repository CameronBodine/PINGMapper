# PINGMapper Ubuntu 22.04 install instruction without using conda

## These installation commands need to be executed only once
`sudo apt install git g++ libgdal-dev python3-dev python3.10-venv python3-tk`

`git clone https://github.com/CameronBodine/PINGMapper.git`

`cd PINGMapper`

`python3 -m venv .venv`

`source .venv/bin/activate`

`pip install -r ubuntu/requirements.txt`

`python ./test_PINGMapper.py 1`

## Afterward, this is required to start PINGMapper again

`cd PINGMapper`

`source .venv/bin/activate`
