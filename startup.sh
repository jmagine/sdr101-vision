#!/bin/bash

SESS='dsm'
echo checking whether $SESS is a tmux session
tmux has-session -t $SESS 2>&1 > /dev/null
if [ $? != 0 ]; then
    echo creating new $SESS session
    SHELL='/bin/bash' tmux new-session -s $SESS -d
    tmux send-keys -t $SESS '/home/pi/DistributedSharedMemory/build/DSMServer -f -s 45' C-m
    echo attach with tmux a -t $SESS
else
    echo tmux session $SESS already exists
fi

SESS='pics'
echo checking whether $SESS is a tmux session
tmux has-session -t $SESS 2>&1 > /dev/null
if [ $? != 0 ]; then
    echo creating new $SESS session
    SHELL='/bin/bash' tmux new-session -s $SESS -d
    tmux send-keys -t $SESS 'take_pics' C-m
    echo attach with tmux a -t $SESS
else
    echo tmux session $SESS already exists
fi
