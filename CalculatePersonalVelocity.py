#!/usr/bin/env python

"""
Script to Calculate my Personal Velocity
Utilities data from icalBuddy

Usage:
- Current week
python ~/code/Misc/CalculatePersonalVelocity.py

- Last week
python ~/code/Misc/CalculatePersonalVelocity.py 1

- Week before last
python ~/code/Misc/CalculatePersonalVelocity.py 2

"""

from __future__ import print_function
from __future__ import division
from subprocess import check_output
import datetime
import sys
from tabulate import tabulate

__author__ = "Ben Mason"
__copyright__ = "Copyright 2017"
__version__ = "0.1"
__email__ = "locutus@the-collective.net"
__status__ = "Production"

DATEFORMAT = '%m/%d/%Y'
DAYLENGTH = 9
DAYSINWEEK = 5
TOTALHOURS = DAYLENGTH * DAYSINWEEK
#Daily Adjust in Mins
DAILYADJUST = 0
DECIMAL_PRECISION=2
ADMINMEETINGS = ["Daily Review", "Lunch", "Weekly Review"]
FOCUSTIME = ["Focus"]
IGNOREEVENTS = ["FW: Managed Services Daily Operations Call",
                "Network Huddle (with recording option)"]
DAYSOFWEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
ICALBUDDYLOC = "/usr/local/bin/icalbuddy"


def datesofweek(weekdelta=0):
    """ Calculate start and end of week """

    weekdelta = weekdelta * 7

    day = datetime.date.today()
    datetoday = datetime.datetime.strptime(day.strftime(DATEFORMAT), DATEFORMAT)
    start = datetoday - datetime.timedelta(days=datetoday.weekday() + weekdelta)
    end = start + datetime.timedelta(days=DAYSINWEEK-1)
    return day, start, end

def timelength(timerange):
    """ Calculate length of meeting """
    try:
        startime, stoptime = timerange.split(" - ")
    except ValueError:
        print ("ERROR: Entry \'" + timerange + "\' problem returning 0")
        return 0
    thetime1 = datetime.datetime.strptime(startime, '%H:%M')
    thetime2 = datetime.datetime.strptime(stoptime, '%H:%M')
    length = thetime2 - thetime1
    lengthmins = length.seconds/60

    return lengthmins

def geticaldata(weekdelta=0):
    """ Run icalBuddy and return list of data """
    _, monday, friday = datesofweek(weekdelta)

    daterange = "eventsFrom:" + monday.strftime(DATEFORMAT) + \
        " to:" + friday.strftime(DATEFORMAT)

    icalbuddycommand = [ICALBUDDYLOC,
                        "-npn",
                        "-ea",
                        "-nc",
                        "-ps ' ~ '",
                        "-df %m/%d/%Y",
                        "-tf %H:%M",
                        "-eep 'url,location,notes,attendees'",
                        "-b ''",
                        "-ic 'Calendar'",
                        daterange,
                        "| uniq"] # using uniq to overcome and macOS bug

    icalbuddyout = check_output(' '.join(icalbuddycommand), shell=True)
    icalbuddyout = icalbuddyout.decode('UTF-8')
    rawlist = icalbuddyout.split('\n')

    return rawlist

def processicaldata(rawlist):
    """ Process a list of ical Buddy Data """

    today, _, _ = datesofweek()

    workdaily = {}
    for item in DAYSOFWEEK:
        workdaily[item] = 0

    admindaily = {}
    for item in DAYSOFWEEK:
        admindaily[item] = 0

    focusdaily = {}
    for item in DAYSOFWEEK:
        focusdaily[item] = 0

    for line in rawlist:
        # print line
        if line != "":
            #print(line)
            event, thedatetime = line.split('~')
            if event not in IGNOREEVENTS:
                # 08/11/2017 at 10:00 - 10:30
                # print (event, thedatetime)
                date, timerange = thedatetime.split(' at ')
                if date == 'today':
                    currdate = datetime.datetime.strptime(today.strftime(DATEFORMAT),
                                                          DATEFORMAT)
                elif date == 'yesterday':
                    yesterday = datetime.date.today() + datetime.timedelta(days=-1)
                    currdate = datetime.datetime.strptime(yesterday.strftime(DATEFORMAT),
                                                          DATEFORMAT)
                elif date == 'tomorrow':
                    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
                    currdate = datetime.datetime.strptime(tomorrow.strftime(DATEFORMAT),
                                                          DATEFORMAT)
                elif date == 'day after tomorrow':
                    tomorrow = datetime.date.today() + datetime.timedelta(days=2)
                    currdate = datetime.datetime.strptime(tomorrow.strftime(DATEFORMAT),
                                                          DATEFORMAT)
                elif date == 'day before yesterday':
                    tomorrow = datetime.date.today() + datetime.timedelta(days=-2)
                    currdate = datetime.datetime.strptime(tomorrow.strftime(DATEFORMAT),
                                                          DATEFORMAT)
                else:
                    # 08/11/2017 at 10:00 - 10:30
                    # currdate = datetime.datetime.strptime(date, '%b %d, %Y')
                    currdate = datetime.datetime.strptime(date, DATEFORMAT)

                if event in ADMINMEETINGS:
                    admindaily[DAYSOFWEEK[currdate.weekday()]] \
                    += timelength(timerange)
                elif event in FOCUSTIME:
                    focusdaily[DAYSOFWEEK[currdate.weekday()]] \
                    += timelength(timerange)
                else:
                    workdaily[DAYSOFWEEK[currdate.weekday()]] \
                    += timelength(timerange)

    return workdaily, admindaily, focusdaily


def printvelocitystats(workdaily, admindaily, focusdaily):
    """ Display ther Velicty Stats """
    totalvelocity = 0
    admintotal = 0
    worktotal = 0
    focustotal = 0
    focus = 0

    dailyheader = ["Day of Week", "Work", "Admin", "Focus", "Total", "Free"]
    dailyrows = []

    for item in DAYSOFWEEK:
        # need daily adjust to account for re-occuring tentatives
        work = (workdaily[item] - DAILYADJUST)/60
        if work != 0:
            admin = admindaily[item]/60
            focus = (focusdaily[item] - DAILYADJUST)/60
        else:
            admin = 0

        admintotal += admin
        worktotal += work
        focustotal += focus
        dailytotal = admin + work + focus
        free = DAYLENGTH - dailytotal
        totalvelocity += dailytotal

        dailyrows.append([item, round(work, DECIMAL_PRECISION), admin, \
            round(focus, DECIMAL_PRECISION), \
            round(dailytotal, DECIMAL_PRECISION), \
            round(free, DECIMAL_PRECISION)])

    print (tabulate(dailyrows, dailyheader, tablefmt="fancy_grid"))
    print (tabulate([["Work Total", round(worktotal, DECIMAL_PRECISION)],
                     ["Admin Total", admintotal],
                     ["Focus Total", focustotal],
                     ["Total Hours", round(totalvelocity, DECIMAL_PRECISION)],
                     ["Percent Usage", \
                     str(round((totalvelocity/TOTALHOURS)*100,DECIMAL_PRECISION)) + " %"],
                     ["Free Time Available", round(TOTALHOURS-(totalvelocity), \
                         DECIMAL_PRECISION)]]))

def main():
    """ Main Processing """

    if len(sys.argv) > 1:
        # Positive number backwards
        weekdelta = int(sys.argv[1])
    else:
        weekdelta=0

    icaldata = geticaldata(weekdelta)
    workdata, admindata, focusdaily = processicaldata(icaldata)
    printvelocitystats(workdata, admindata, focusdaily)

if __name__ == "__main__":
    main()
