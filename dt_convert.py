#!/usr/bin/env python3
#dt = "2023-01-26T19:59:35.389z"
from datetime import datetime, timezone
 

def convert_time(bigid_str):
    # expecting format like "2023-01-26T19:59:35.389z"

    bigid_str = bigid_str[:-1]
    dt = bigid_str.split("T")
    mydate = dt[0].split("-")
    year = mydate[0]
    month = mydate[1]
    day = mydate[2]
    mytime = dt[1].split(":")
    hour = mytime[0]
    minute = mytime[1]
    s_ms = mytime[2].split('.')
    second = s_ms[0]
    millisecond = s_ms[1]
    #print(f"{year, month, day, hour, minute, second, millisecond}")
    actual = datetime(int(year), int(month), int(day), int(hour),
                    int(minute), int(second), int(millisecond), tzinfo=timezone.utc)

    epoch =  datetime(1970, 1, 1, tzinfo=timezone.utc)
    x = int((actual - epoch).total_seconds() * 1000)   
    return x

if __name__ == '__main__':
    mydt = "2023-01-26T19:59:36.389z"
    print(f"Original: {mydt}")
    x = convert_time(mydt)
    print(x)

    # note: in CloudWatch Logs console, the UI will show the timestamp with a +/- to show the local time zone