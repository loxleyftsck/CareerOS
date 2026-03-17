import json
import os

DB_FILE = 'careeros_db.json'

def save_jobs(jobs):
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
                
    # deduplicate by title
    existing_titles = {j['title'] for j in data}
    for j in jobs:
        if j['title'] not in existing_titles:
            data.append(j)
            existing_titles.add(j['title'])
            
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_jobs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []
