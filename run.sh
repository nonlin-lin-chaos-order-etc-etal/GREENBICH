cd /home/user/vcs/ircbot_greenbich/

echo pwd
pwd
echo whoami
whoami

. pythonvars.sh

# export CL="strace ./venv/bin/python ./launch_all.py"
export CL="./venv3sn2/bin/python ./launch_all.py"
echo "launching $CL"
$CL


