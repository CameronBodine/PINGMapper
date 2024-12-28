@echo off
REM Activate the conda environment
call conda activate ~/miniconda3/envs/ping
if ERRORLEVEL 1 (
    goto except_block_lowAnaconda
)
goto run_script

:except_block_lowAnaconda
call conda activate ~/anaconda3/envs/ping
if ERRORLEVEL 1 (
    goto except_block_Anaconda
)
goto run_script

:except_block_Anaconda
call conda activate ~/Anaconda3/envs/ping
if ERRORLEVEL 1 (
    echo Error! Cannot load Conda environment.
)
goto run_script

:run_script
REM Run the Python script
python test_PINGMapper.py 1