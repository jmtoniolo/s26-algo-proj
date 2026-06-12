#!/usr/bin/bash

TECH_ARG=""
TECHS_ARG="--technicians 3"


python3 main.py $TECHS_ARG fifo /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label fifo-nm5
python3 main.py $TECHS_ARG fifo /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label fifo-nm8
python3 main.py $TECHS_ARG fifo /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_uniform.20260611192737438690.csv --label fifo-unif

python3 main.py $TECHS_ARG priority /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label priority-nm5
python3 main.py $TECHS_ARG priority /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label priority-nm8
python3 main.py $TECHS_ARG priority /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_uniform.20260611192737438690.csv --label priority-unif

python3 main.py $TECHS_ARG sjf /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label sjf-nm5
python3 main.py $TECHS_ARG sjf /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label sjf-nm8
python3 main.py $TECHS_ARG sjf /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_uniform.20260611192737438690.csv --label sjf-unif

python3 main.py $TECHS_ARG greedy /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label greedy-nm5
python3 main.py $TECHS_ARG greedy /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label greedy-nm8
python3 main.py $TECHS_ARG greedy /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_uniform.20260611192737438690.csv --label greedy-unif

python3 main.py $TECHS_ARG dp /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label dp-nm5
python3 main.py $TECHS_ARG dp /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label dp-nm8
python3 main.py $TECHS_ARG dp /home/jmtoniolo/scratch/s26-algo/s26-algo-proj/synthetic_job_list_priority_uniform.20260611192737438690.csv --label dp-unif
