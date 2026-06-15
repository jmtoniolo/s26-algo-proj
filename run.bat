@echo off
REM Batch file to run algorithm analysis project

SET TECHS_ARG=--technicians 5

REM FIFO Algorithm
python main.py %TECHS_ARG% fifo synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label fifo-nm5
python main.py %TECHS_ARG% fifo synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label fifo-nm8
python main.py %TECHS_ARG% fifo synthetic_job_list_priority_uniform.20260611192737438690.csv --label fifo-unif

REM Priority Algorithm
python main.py %TECHS_ARG% priority synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label priority-nm5
python main.py %TECHS_ARG% priority synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label priority-nm8
python main.py %TECHS_ARG% priority synthetic_job_list_priority_uniform.20260611192737438690.csv --label priority-unif

REM Shortest Job First Algorithm
python main.py %TECHS_ARG% sjf synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label sjf-nm5
python main.py %TECHS_ARG% sjf synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label sjf-nm8
python main.py %TECHS_ARG% sjf synthetic_job_list_priority_uniform.20260611192737438690.csv --label sjf-unif

REM Greedy Algorithm
python main.py %TECHS_ARG% greedy synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label greedy-nm5
python main.py %TECHS_ARG% greedy synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label greedy-nm8
python main.py %TECHS_ARG% greedy synthetic_job_list_priority_uniform.20260611192737438690.csv --label greedy-unif

REM Dynamic Programming Algorithm
python main.py %TECHS_ARG% dp synthetic_job_list_priority_normal_mean5.20260611192737454689.csv --label dp-nm5
python main.py %TECHS_ARG% dp synthetic_job_list_priority_normal_mean8.20260611192737466968.csv --label dp-nm8
python main.py %TECHS_ARG% dp synthetic_job_list_priority_uniform.20260611192737438690.csv --label dp-unif
