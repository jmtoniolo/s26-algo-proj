#!/usr/bin/bash

python3 main.py fifo nm5 --label fifo-nm5
python3 main.py fifo nm8 --label fifo-nm8
python3 main.py fifo unif --label fifo-unif

python3 main.py priority nm5 --label priority-nm5
python3 main.py priority nm8 --label priority-nm8
python3 main.py priority unif --label priority-unif

python3 main.py sjf nm5 --label sjf-nm5
python3 main.py sjf nm8 --label sjf-nm8
python3 main.py sjf unif --label sjf-unif

python3 main.py greedy nm5 --label greedy-nm5
python3 main.py greedy nm8 --label greedy-nm8
python3 main.py greedy unif --label greedy-unif
