import pandas as pd
import json

df = pd.read_csv('allotment_result.csv')

df['All India Rank'] = pd.to_numeric(df['All India Rank'], errors='coerce')
df = df.dropna(subset=['All India Rank'])

known_cats = [
    'UR PwD', 'SC PwD', 'ST PwD', 'EWS PwD', 
    'OBC-A (Non- Creamy Layer) PwD', 'OBC-B (Non- Creamy Layer) PwD', 
    'UR', 'SC', 'ST', 'EWS', 
    'OBC-A (Non- Creamy Layer)', 'OBC-B (Non- Creamy Layer)', 
    'OBC (Non-Creamy Layer)'
]

def get_allotted(val):
    val = str(val).strip()
    for k in known_cats:
        if val.startswith(k):
            return k
    return "UR"

df['Allotted_Cat_Clean'] = df['Allotted/Candidate Category'].apply(get_allotted)

cutoffs = df.groupby(['Institute', 'Course', 'Allotted Quota', 'Allotted_Cat_Clean'])['All India Rank'].max().reset_index()

data = cutoffs.to_dict(orient='records')

with open('data.js', 'w') as f:
    f.write('const collegeData = ' + json.dumps(data) + ';')

print(f"Generated data.js with {len(data)} cutoff records.")
