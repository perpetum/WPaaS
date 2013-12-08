#/usr/bin/ksh
echo "This script installs the AIX box for Flask/Redis/Celery dev env."

PROXY=xxxxxxxx:8080
export http_proxy=$PROXY

#Install all the RPMS needed
rpm -ivh --nodeps gettext-0.17-8.aix6.1.ppc.rpm
rpm -ivh \
bash-4.2-7.aix6.1.ppc.rpm \
bzip2-1.0.6-2.aix6.1.ppc.rpm \
coreutils-8.21-1.aix6.1.ppc.rpm \
curl-7.28.0-1.aix6.1.ppc.rpm \
db-4.8.24-4.aix6.1.ppc.rpm \
expat-2.1.0-1.aix6.1.ppc.rpm \
gdbm-1.10-1.aix6.1.ppc.rpm \
gmp-5.1.3-1.aix6.1.ppc.rpm \
info-5.0-2.aix6.1.ppc.rpm \
libffi-3.0.11-1.aix6.1.ppc.rpm \
libiconv-1.14-1.aix6.1.ppc.rpm \
libidn-1.24-1.aix6.1.ppc.rpm \
libssh2-1.4.2-1.aix6.1.ppc.rpm \
logrotate-3.8.3-1.aix6.1.ppc.rpm \
ncurses-5.9-3.aix6.1.ppc.rpm \
openssl-1.0.0k-2.aix6.1.ppc.rpm \
pcre-8.12-3.aix6.1.ppc.rpm \
popt-1.16-2.aix6.1.ppc.rpm \
python-2.7.5-4.aix6.1.ppc.rpm \
python-setuptools-0.9.8-1.aix6.1.noarch.rpm \
python-virtualenv-1.10.1-1.aix6.1.noarch.rpm \
readline-6.2-3.aix6.1.ppc.rpm \
redis-2.6.16-1.aix5.2.ppc.rpm \
sqlite-3.7.15.2-2.aix6.1.ppc.rpm \
wget-1.14-1.aix6.1.ppc.rpm \
zlib-1.2.5-6.aix6.1.ppc.rpm

#Create your Python virtual env.
virtualenv flask

#Then Install Celery
pip --proxy ecfrec.frec.bull.fr:8080 install -U celery

#Then Install Sphinx (doc si besoin)
pip --proxy ecfrec.frec.bull.fr:8080 install -U Sphinx

#Then prepare your env (update your shell startup script)
export C_FORCE_ROOT=true
export http_proxy=ecfrec.frec.bull.fr:8080
export PATH=/home/misoard/flask/bin:$PATH

#To run Celery worker:
cd $WPAR_ENV
celery -A tasks worker --loglevel=info

#To run WPARs ReST in Peace:
cd $WPAR_ENC
./wpars.py
