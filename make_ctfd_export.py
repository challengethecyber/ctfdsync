import argparse
import csv
import io
import json

parser = argparse.ArgumentParser()
parser.add_argument('file', type=argparse.FileType('rb'))
args = parser.parse_args()

standings = []

with io.TextIOWrapper(args.file, encoding='utf-8') as results_file:
    reader = csv.DictReader(results_file)

    for row in reader:
        if not row['place']:
            continue

        standings.append({
            "pos": int(row['place']),
            "team": row['team'],
            "score": int(row['score'])
        })

print(json.dumps({"standings": standings}))