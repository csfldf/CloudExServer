#!/usr/bin/expect
#本函数的用法时 changeCeilometerInterval.sh ipEnd period(unit:second) windowSize
set timeout 30

set ipEnd [lindex $argv 0]

spawn ssh root@192.168.0.${ipEnd}
expect "password:"
send "123\r"

expect "@ubuntu-"
send "cd PMUtil\r"
expect "@ubuntu-"
send "./util.py 0 > ./result.data\r"
expect "@ubuntu-"
send "scp result.data sk@192.168.0.90:/home/sk/cloudEx/tmpData/\r"
expect "@ubuntu-"
send "exit\r"
expect eof
exit

