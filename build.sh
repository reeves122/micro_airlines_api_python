#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

rm -r build
mkdir build

docker run -v ${DIR}:/opt/build_source python:3.7 /bin/bash -c "cd /opt/build_source; pip3 install -t ./build -r requirements.txt"

rsync -avr --exclude='build/' --exclude='terraform/' --exclude='venv/' --exclude='.git/' --exclude='.idea/' . build/

cd build/
zip -r ../terraform/package.zip .

