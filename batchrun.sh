#!/usr/bin/bash

python3 main.py fifo nm5
python3 main.py fifo nm8
python3 main.py fifo unif

python3 main.py priority nm5
python3 main.py priority nm8
python3 main.py priority unif

python3 main.py sjf nm5
python3 main.py sjf nm8
python3 main.py sjf unif

python3 main.py greedy nm5
python3 main.py greedy nm8
python3 main.py greedy unif