import os
all=6
count=0
file1=os.system('$ENGINE/engine ../tests/json/query-dns-udp.json ../tests/trace-2012.ftz -v 1 | grep "No. of Filtered Records:"')
file2=os.system('$ENGINE/engine ../output/query-dns-udp-parsed.json ../tests/trace-2012.ftz -v 1| grep "No. of Filtered Records:"')
if (file1==file2):
    count=count+1
    print("OK!")

file3=os.system('$ENGINE/engine ../tests/json/query-http-octets.json ../tests/trace-2012.ftz -v 1 | grep "No. of Filtered Records:"')
file4=os.system('$ENGINE/engine ../output/query-http-octets-parsed.json ../tests/trace-2012.ftz -v 1| grep "No. of Filtered Records:"')
if (file3==file4):
    count=count+1
    print("OK!")

file5=os.system('$ENGINE/engine ../tests/json/query-https-tcp-session.json ../tests/trace-2012.ftz -v 1 | grep "No. of Filtered Records:"')
file6=os.system('$ENGINE/engine ../output/query-https-tcp-session-parsed.json ../tests/trace-2012.ftz -v 1| grep "No. of Filtered Records:"')
if (file5==file6):
    count=count+1
    print("OK!")
