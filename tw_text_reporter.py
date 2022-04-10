#!/usr/bin/env python3
'''
    This parses all tasks with in a time frame for specific text and total the time tracked
    Author: Ben Mason
'''

__author__ = "Ben Mason"
__copyright__ = "Copyright 2022"
__version__ = "1.0.0"
__email__ = "locutus@the-collective.net"
__status__ = "Production"


import subprocess
import json
import logging
import argparse
from datetime import datetime, timedelta


DURATION = ":lastyear"
CLI_BASE_COMMAND = 'timew'
LOGGING_LEVEL = logging.ERROR
LOGGING_FORMAT = '[%(levelname)s] %(asctime)s - %(funcName)s %(lineno)d - %(message)s'

class TwReporter:
    ''' Collect list of tasks functions for reporting '''

    no_of_tasks_tracked = 0
    todays_tasks = None

    @staticmethod
    def execute_cli(cli: list) -> str:
        ''' Execute commands on CLI returns STDOUT '''

        logging.debug("cli: %s", cli)

        process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        logging.debug("stdout: %s", stdout)
        logging.debug("stderr: %s", stderr)

        return stdout


    def collect_tasks_list(self, duration='day') -> int:
        '''
        Collect list of tracked tasks (default to today)
        Store in object variable

        return number of tasks
        '''

        table_dict = []
        date_format = "%Y%m%dT%H%M%SZ"


        cli = [CLI_BASE_COMMAND, 'export', ':'+duration]
        logging.debug("cli: %s", cli)

        stdout = self.execute_cli(cli)

        task_list = json.loads(stdout)

        for task_item in task_list:
            task = {}

            task['starttime'] = datetime.strptime(task_item['start'], date_format)

            # Calculate Duration (skip or active)
            if 'end' in task_item.keys():
                task['stoptime'] = datetime.strptime(task_item['end'], date_format)
                task['duration'] = task['stoptime'] - task['starttime']
            else:
                task['duration'] = 'Active'

            task['id'] = task_item['id']
            task['tag'] = task_item.get('tags', [''])

            table_dict.append(task)

        self.todays_tasks = table_dict
        self.no_of_tasks_tracked = len(table_dict)

        return len(table_dict)

    def parse_tags_for_text(self, text: str) -> list:
        ''' Parse through list of tasks for specified text '''

        matched_tasks = []

        for i in self.todays_tasks:
            if text.lower() in ', '.join(i['tag']).lower():
                matched_tasks.append(i)
                print(f"{i['starttime'].strftime('%m/%d/%Y')} - {', '.join(i['tag'])} - {i['duration']}")

        return matched_tasks

    @staticmethod
    def add_durations(task_list: list) -> timedelta:
        ''' Total all of the time from list of tasks'''

        total_duration = timedelta()

        for i in task_list:
            logging.debug("i['duration']: %s", i['duration'])
            total_duration += i['duration']

        return total_duration


def main():
    ''' Main function '''

    parser = argparse.ArgumentParser(description='Search for text')
    parser.add_argument('search_text', metavar='text', type=str, help='Test to Search')
    parser.add_argument('--tw_duration', '-t', default='lastyear', help='duration to search')

    args = parser.parse_args()

    print (f"""Searching for {args.search_text}
During the timeframe: {args.tw_duration}
    """)
    logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)

    twrep = TwReporter()

    twrep.collect_tasks_list(duration=args.tw_duration)
    matched_tasks = twrep.parse_tags_for_text(args.search_text)
    total_duration = twrep.add_durations(matched_tasks)
    print("")
    print(f"Total Time Tracked: {total_duration}")

####### Start Main Function #############
if __name__ == "__main__":
    main()
