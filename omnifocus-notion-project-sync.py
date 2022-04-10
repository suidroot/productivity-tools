#!/usr/bin/env python3
'''
Script to Syncronize Projects between Omnifocus and Notion Project database
'''
import csv
import json
import logging
import requests
import notionconfig


__author__ = "Ben Mason"
__copyright__ = "Copyright 2022"
__version__ = "1.0.0"
__email__ = "locutus@the-collective.net"
__status__ = "Production"

BASE_URL = "https://api.notion.com/v1"
LOGGING_LEVEL = logging.ERROR
LOGGING_FORMAT = '[%(levelname)s] %(asctime)s - %(funcName)s %(lineno)d - %(message)s'

SKIPLIST = ["Template", None ]

of_task_status_mapping = {
    "active status" : "In Progress",
    "done status" : "Complete",
    "dropped status" : "Dropped",
    "on hold status" : "Hold"
}

# Map Tag to Relm
of_relm_mapping = {
    "Personal" : "Personal",
    "HouseHold" : "Household",
    "Projects" : "Personal",
    "Education" : "Education",
    "Work" : "Work",
    "Template" : "Template",
    "Personal Projects" : "Hobby"
}

class NotionInterface:
    ''' This class is used as an interface to the Notion API '''

    instance_name = None
    api_key = None

    def __init__(self, instance_name, api_key):
        ''' Initialize class '''
        self.instance_name = instance_name
        self.api_key = api_key

    def execute_request(self, method, url, payload):
        ''' Execute REST API calls '''

        headers = {
        'Notion-Version': '2021-08-16',
        'Authorization': self.api_key,
        'Content-Type': 'application/json'
        }

        response = requests.request(method, url, headers=headers, data=payload)

        # TODO: Error Handling
        return json.loads(response.text)


    def search_database_by_text_property(self, database_id, proj_property, value):
        ''' Use Notion API to query by text propery in Database '''

        url = BASE_URL + "/databases/" + database_id + "/query"

        payload = json.dumps({
        "filter": {
            "property": proj_property,
            "text": {
            "contains": value
            }
        }
        })

        result = self.execute_request('POST', url, payload)

        return result


    def create_page_db(self, page_parameters):
        ''' Use Notion API to create new Project item in Notion Database '''

        url = BASE_URL + "/pages"

        payload = json.dumps({
        "parent": {
            "database_id": page_parameters['databaseid']
        },
        "properties": {
            "Name": {
            "title": [
                {
                    "text": {
                        "content" : page_parameters['name']
                    }
                }
            ]
            },
            "Status": {
                "select": {
                    "name" : page_parameters['status']
                }
            },
            "Relm": {
                "select": {
                    "name" : page_parameters['relm']
                }
            },
            "OmnifocusId": {
                "rich_text": [
                    {
                    "text" :{
                        "content" : page_parameters['ofid']
                    }
                } ]
            },
        },
        "children": []
        })

        result = self.execute_request('POST', url, payload)
        logging.debug(result)

        return result

    def update_page_status(self, page_id, status):
        ''' Use Notion API to update status on a Project page '''

        url = BASE_URL + "/pages/" + page_id

        payload = json.dumps({
        "properties": {
            "Status": {
            "select": {
                "name": status
            }
            }
        }
        })
        result = self.execute_request('PATCH', url, payload)

        return result

    def check_if_project_exists(self, task: dict, databaseid) -> dict:
        ''' Query Notion API to see of a Task exists with the ofid '''

        search_result = self.search_database_by_text_property(databaseid, \
            "OmnifocusId", task['ofid'])
        logging.debug(search_result)

        results = { }

        if search_result['object'] != 'error' and search_result['results'] != []:
            results['projid'] = search_result['results'][0]['id']
            results['projstatus'] = search_result['results'][0]['properties']['Status']\
                ['select']['name']
            results['projname'] = search_result['results'][0]['properties']['Name']\
                ['title'][0]['text']['content']
            logging.debug ("%s", results)

        else:
            #create
            results = None

        return results

def read_of_csv_file(of_csv_filename):
    ''' Read in CSV export file of OmiFocus projects generated from assicated applescript '''

    def clean_tag(tag):
        tag = tag.strip("?")
        tag = tag.strip(" ")

        return tag

    # "ofid","Status","Name","relm","tag","Note"

    of_data_list = []
    with open(of_csv_filename, newline='', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',') #, quotechar='"')
        for row in reader:

            row['tag'] = clean_tag(row['tag'])

            of_data_list.append(row)

    logging.debug(of_data_list)

    return of_data_list

def task_status_mapper(of_task_text: str, status_mapping: dict) -> str:
    ''' Normalize Project status to assoicated Notion state '''

    try:
        status = status_mapping[of_task_text]
    except KeyError:
        logging.error("Status Error: ", of_task_text)
        status = None

    return status

def task_relm_mapper(of_folder_text: str, relm_mapping: dict) -> str:
    ''' Normalize Project relm to assoicated Notion relm '''

    try:
        relm = relm_mapping[of_folder_text]
    except KeyError:
        logging.error("Relm Error: ", of_folder_text)
        relm = None

    return relm

def notion_database_stuff(notion_if, task, database):
    ''' Check for Project in DB and Update or create it '''

    notion_results = notion_if.check_if_project_exists(task, database)
    if notion_results is None:
        logging.debug("Creating task %s", task)

        page_parameters= {
            'databaseid' : database,
            'status' : task['status'],
            'name' : task['name'],
            'ofid' : task['ofid'],
            'relm' : task_relm_mapper(task['relm'], of_relm_mapping)
        }
        notion_if.create_page_db(page_parameters)
    else:
        if notion_results['projstatus'] != task['status']:
            logging.debug("Updating Status for task %s", task)
            notion_if.update_page_status(notion_results['projid'], task['status'])

def main():
    ''' Main Function '''

    logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)

    notion_if = NotionInterface(notionconfig.NOTION_ID, notionconfig.API_KEY)

    of_tasklist = read_of_csv_file(notionconfig.OF_CSV_FILENAME)

    for task in of_tasklist:
        task['status'] = task_status_mapper(task['status'], of_task_status_mapping)
        logging.debug(task)

        if task['tag'] in SKIPLIST or task['relm'] in SKIPLIST or "notion: skip" in task['note']:
            logging.debug("Skipping Notion Check")
        else:
            #https://www.notion.so/suidroot/4d4430579537403cb77007746d19268b?v=985bb580f90e401b8456193b2a1deb9f

            if task['relm'] == 'Work':
                logging.debug("Work task")
                notion_database_stuff(notion_if, task, notionconfig.work_db)
            else:
                notion_database_stuff(notion_if, task, notionconfig.DATABASE_ID)

       


if __name__ == '__main__':
    main()
