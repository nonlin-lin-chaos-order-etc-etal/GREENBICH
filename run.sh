cd /home/user/git/ircbot_greenbich/

echo pwd
pwd

export PYTHONHOME=/home/user/vcs/greenbich-runtime/venv3_2/lib/python3.6

CL=./venv3_2/bin/python launch_all.py
echo "launching $CL"
$CL

