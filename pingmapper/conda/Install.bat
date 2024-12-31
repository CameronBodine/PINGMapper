@echo off
REM Create ping environment
echo Creating ping environment
call conda env create --file ./conda/PINGMapper.yml -y