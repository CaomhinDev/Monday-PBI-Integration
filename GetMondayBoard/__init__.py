import logging
import requests
import json
import time
import re
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        key = req_body.get('key')
        board_id = req_body.get('board_id')
        correct_pw = r"some_s3Cur3_fruity!" # Change this.
        auth = bool(re.search(correct_pw,req_body.get('func_pw')))

    if auth:
        MONDAY_ENDPOINT = "https://api.monday.com/v2/"
        full_data_for_pbi = []
        done = False
        loop_failsafe = 0
        headers = {"Authorization":key,"Content-Type":"application/json"}
        page = 1
        while(not done):
            loop_failsafe += 1
            if(loop_failsafe >= 100):
                done=True
            query = '{"query": " {complexity { query, after, reset_in_x_seconds  }  boards(ids: '+ board_id + ')  { id name items (limit: 30, page:'+ str(page) +') {id, name, updated_at, group { title }, column_values { title, text } subitems { name column_values { title, text } } } }}"}'
            data_request = requests.post(MONDAY_ENDPOINT, headers=headers, data=query)
            resp_json = json.loads(data_request.text)
            complexity_error = 'error_message' in resp_json and 'ComplexityException' in resp_json['error_code']
            if(complexity_error):
                reset_time = re.findall(r'reset in (\d+) seconds',resp_json['error_message'])[0]
                print("Sleeping for " + str(reset_time))
                time.sleep(int(reset_time))
            else:
                if(resp_json['data']['boards'][0]['items']):
                    full_data_for_pbi.append(resp_json)
                    if(resp_json['data']['complexity']['query'] > resp_json['data']['complexity']['after']): # If there's not enough complexity left, sleep for required duration.
                        time.sleep(resp_json['data']['complexity']['reset_in_x_seconds']+1)     
                else:
                    done = True
                page += 1
        return func.HttpResponse(json.dumps(full_data_for_pbi))
    else:
        return func.HttpResponse(
             "Auth Error",
             status_code=200
        )
