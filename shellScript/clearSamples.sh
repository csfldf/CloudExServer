#!/bin/bash


mongo --host 192.168.0.40 ceilometer --eval "db.meter.remove();"
