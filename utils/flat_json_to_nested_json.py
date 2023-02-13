#!/usr/bin/env python

import json
import sys

json_cfg = {}
with open(sys.argv[1], 'r') as file_cfg:
    json_cfg = json.loads(file_cfg.read())

nested_cfg = {}

for k, v in json_cfg.items():
    cursor = nested_cfg 
    depth = 1
    segments = k.split('.')
    
    for segment in segments:
        if segment not in cursor:
            cursor[segment] = {}
        if depth == len(segments):
            cursor[segment] = v
        cursor = cursor[segment]
        depth += 1

print(json.dumps(nested_cfg, indent=2))