# Example: python batch.py 2020-01-01 2020-01-02
import os
import sys
from datetime import date, timedelta, datetime

if len(sys.argv) == 3:
    sdate = datetime.strptime(sys.argv[1], '%Y-%m-%d')   # start date
    edate = datetime.strptime(sys.argv[2], '%Y-%m-%d')   # end date
else:
    sdate = date(2020, 1, 1)   # start date
    edate = date(2020, 1, 1)   # end date

delta = edate - sdate       # as timedelta

for i in range(delta.days + 1):
    day = sdate + timedelta(days=i)
    day = day.strftime('%Y%m%d')
    print(day)
    os.system('./fetch_data.sh ' + day)
    os.system('mv ' + day + '_raw.txt ./data/')
    os.system('python extract_data.py ' + day)
    os.system('rm ./data/' + day + '_raw.txt')
    os.system('rm ./data/' + day + '_graph.gpickle')

