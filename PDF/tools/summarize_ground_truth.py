#!/usr/bin/env python3
import json, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
gt=json.loads((root/'ground_truth'/'ground_truth.json').read_text(encoding='utf-8'))
print('corpus:', gt['corpus_id'])
print('items:', len(gt['items']))
labels={}
for item in gt['items']:
    labels[item['expected_label']] = labels.get(item['expected_label'],0)+1
for k,v in sorted(labels.items()):
    print(f'{k}: {v}')
