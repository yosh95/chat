#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import requests

API_KEY = os.getenv("OPENAI_API_KEY")
if API_KEY is None:
    print("OPENAI_API_KEY environment variable must be set.")
    exit(1)
API_URL = "https://api.openai.com/v1/models"

parser = argparse.ArgumentParser()
parser.add_argument("models", nargs="*")
parser.add_argument("-v",
                    action="store_true",
                    help="Verbose output")
args = parser.parse_args()
verbose = args.v

headers = {
        "Authorization": f"Bearer {API_KEY}"
        }
response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    result = response.json()

    if 'data' in result:
        if len(args.models) == 0:
            if verbose is False:
                model_list = {}
                for model in result['data']:
                    name = model['id']
                    created_datetime = datetime.datetime.fromtimestamp(
                            model['created'])
                    formatted_created = created_datetime.strftime(
                            '%Y/%m/%d %H:%M:%S')
                    model_list[model['id']] = formatted_created

                    sorted_model_list = sorted(model_list.items(),
                                               key=lambda item: item[1])

                for name, created in sorted_model_list:
                    print(f"{name}: {created}")

            else:
                json_str = json.dumps(result, ensure_ascii=False, indent=2)
                print(json_str)
        else:
            for model in result['data']:
                name = model['id']
                if name in args.models:
                    json_str = json.dumps(model, ensure_ascii=False, indent=2)
                    print(json_str)

else:
    json_str = json.dumps(response.json(), ensure_ascii=False, indent=2)
    print(json_str)
