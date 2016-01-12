#!/usr/bin/expect
#本函数的用法时 changeCeilometerInterval.sh ipEnd period(unit:second) windowSize
set timeout 30

set ttl [lindex $argv 0]


spawn ssh root@192.168.0.40
expect "password:"
send "123\r"

expect "@ubuntu-"
send "openstack/openstackInstall/telemetry/setMeterTTL.sh\r"
expect "meter ttl"
send "${ttl}\r"



send "exit\r"
expect eof
exit

