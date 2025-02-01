#!/usr/bin/env python3

import argparse
import json
import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY is None:
    print("GEMINI_API_KEY environment variable must be set.")
    exit(1)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models" \
          + "?key=" + API_KEY

parser = argparse.ArgumentParser()
parser.add_argument("models", nargs="*")
parser.add_argument("-v",
                    action="store_true",
                    help="Verbose output")
args = parser.parse_args()
verbose = args.v

response = requests.get(API_URL)

if response.status_code == 200:
    result = response.json()

    if 'models' in result:
        if len(args.models) == 0:
            if verbose is False:
                for model in result['models']:
                    name = model['name'].split("/")[1]
                    print(name)
            else:
                json_str = json.dumps(result, ensure_ascii=False, indent=2)
                print(json_str)
        else:
            for model in result['models']:
                name = model['name'].split("/")[1]
                if name in args.models:
                    json_str = json.dumps(model, ensure_ascii=False, indent=2)
                    print(json_str)

else:
    json_str = json.dumps(response.json(), ensure_ascii=False, indent=2)
    print(json_str)
