set -o vi
export C_FORCE_ROOT=true
export http_proxy=ecfrec.frec.bull.fr:8080
export PATH=/opt/freeware/bin:/home/misoard/flask/bin:$PATH 

celery -A tasks worker --loglevel=info
./wpars.py
