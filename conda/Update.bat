@echo off
REM Create ping environment
echo Updating base environment
call conda update -y -n base conda
call conda clean -y --all
call python.exe -m pip install --upgrade pip

conda env update --file ./conda/PINGMapper.yml --prune
