#!/bin/bash

cd $(dirname $0)

MODE=$1

#check for empty mode
if [ -z "$MODE" ];
then
	echo "No mode specified"
	echo "usage: ./configure.sh [live|read|loop]"
	exit 1
fi

echo "DIR $(pwd)/" > config.cfg
echo "MODE ${MODE}" >> config.cfg
cat config.cfg
