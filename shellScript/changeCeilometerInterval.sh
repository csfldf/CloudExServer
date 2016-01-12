#!/usr/bin/expect
#本函数的用法时 changeCeilometerInterval.sh ipEnd period(unit:second) windowSize
set timeout 30
set ipEnd [lindex $argv 0]
set period [lindex $argv 1]
set windowSise [lindex $argv 2]

spawn ssh root@192.168.0.$ipEnd
expect "password:"
send "123\r"

expect "@ubuntu-"
send "openstack/openstackInstall/telemetry/setComputePipeLine.sh\r"
expect "meter period"
send "${period}\r"


expect "window size"
send "${windowSise}\r"

send "exit\r"
expect eof
exit

