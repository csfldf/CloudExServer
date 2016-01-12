#!/bin/bash

serverPid=$(ps aux | awk '$NF=="/home/sk/cloudEx/wsgi_instance/service.py"{print $2}') 

if [ ! -z "$serverPid" ]; then
    kill -15 $serverPid
    echo 'stop server successfully'
else
    echo 'server is not running now!'
fi

