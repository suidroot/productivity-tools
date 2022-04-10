#!/usr/bin/env python

import csv
import subprocess
from taskw import TaskWarrior

DRYRUN = "" 
#DRYRUN = True

OFCSV = "/Users/benmason/Desktop/OmniFocus.csv"

w = TaskWarrior()
# Task ID,Type,Name,Status,Project,Context,Start Date,Due Date,Completion Date,Duration,Flagged,Notes
with open(OFCSV, 'rU') as filehandle:
    reader = csv.reader(filehandle, dialect='excel', quotechar='"')
    for line in reader:
        if line[1] == 'Action':
            project = line[4]
            task = line[2]
            context = '+@'+line[5].replace(" ", "")
            startdate = line[6]
            duedate = line[7]
            duration = line[9]
            note = line[11]
            tags = line[12].split(", ")


# Built-in attributes are:
#   description:    Task description text
#   status:         Status of task - pending, completed, deleted, waiting
#   project:        Project name
#   priority:       Priority
#   due:            Due date
#   recur:          Recurrence frequency
#   until:          Expiration date of a task
#   limit:          Desired number of rows in report, or 'page'
#   wait:           Date until task becomes pending
#   entry:          Date task was created
#   end:            Date task was completed/deleted
#   start:          Date task was started
#   scheduled:      Date task is scheduled to start
#   modified:       Date task was last modified
#   depends:        Other tasks that this task depends upon

            #command = "task add project:\"" + project + "\" tags:\"" + ',"'.join(tags) + "\" " + task
            
            
            command = ["task","add", "project:\"" + project + "\"", "tags:\"" + '","'.join(tags)+"\"",task]
            if DRYRUN == True:
                print command
            else:
                print command
                output = subprocess.check_output(command)
                print output

                #currtask = w.task_add(task, project=project, tags=tags)

                #if duedate != '':
                #    id, task = w.get_task(id=currtask['id'])
                #    task['due'] = duedate
                #    date.append("due="+duedate)
                #if startdate != '':
                #    id, task = w.get_task(id=currtask['id'])
                #    task['due'] = duedate
                #    date.append("scheduled:"+startdate)

                #if duration != '':
                #    id, task = w.get_task(id=currtask['id'])
                #    task['due'] = duedate

# Task ID,Type,Name,Status,Project,Context,Start Date,Due Date,Completion Date,Duration,Flagged,Notes
# 1,Project,Miscellaneous,active,,,,,,,0,
# 1.1,Action,Check on finances,,Miscellaneous,Scheduled,2017-06-12 12:00:00 +0000,,,,0,
