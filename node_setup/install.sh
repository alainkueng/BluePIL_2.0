#!/bin/bash

sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev gcc gfortran python-dev libopenblas-dev liblapack-dev cython libfreetype6-dev


wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz
tar xvf Python-3.8.3.tgz
cd Python-3.8.3
./configure --enable-optimizations --with-ensurepip=install
make -j4
sudo make altinstall
cd ..
sudo rm -rf Python-3.8.3
sudo rm -rf Python-3.8.3.tgz
sudo /sbin/ldconfig

sudo python3.8 -m venv venv
source venv/bin/activate
sudo pip3.8 install Cython
sudo pip3.8 install pyusb
sudo pip3.8 install numpy
sudo pip3.8 install scipy
sudo pip3.8 install matplotlib==2.2.4
sudo pip3.8 install filterpy
sudo pip3.8 install streamz

