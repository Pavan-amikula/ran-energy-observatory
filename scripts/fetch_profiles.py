"""Reproduce the separately licensed measurement-derived traffic subset."""
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
COMMIT='da1db1963b22437aadf6621d6d6c88ffbe2425f7'
BASE=f'https://raw.githubusercontent.com/arimvydas/mob-traffic-ds/{COMMIT}/'

def main():
    with urlopen(BASE+'data/traffic_normal.csv',timeout=30) as r:raw=r.read()
    reader=csv.DictReader(io.StringIO(raw.decode()))
    fields=['t_day']+[f'thp_{day}_milan13_w{week}_sid4259' for week in [1,2,3] for day in ['mon','tue','wed','thu','fri','sat','sun']]
    rows=[{k:row[k] for k in fields} for row in reader]
    assert len(rows)==144
    with (ROOT/'data'/'milan_profiles.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    (ROOT/'data'/'provenance.json').write_text(json.dumps({'source_url':BASE+'data/traffic_normal.csv','source_commit':COMMIT,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'description':'Published measurement-derived normalized Milan internet activity profiles, square 4259, 3 week labels x 7 days x 144 ten-minute bins. Not raw bytes, PRBs or power.',
        'original_source':'https://doi.org/10.7910/DVN/EGZHFV','source_license':'GPL-3.0; underlying Telecom Italia data ODbL-1.0',
        'subset_sha256':hashlib.sha256((ROOT/'data'/'milan_profiles.csv').read_bytes()).hexdigest()},indent=2))
    with urlopen(BASE+'LICENSE',timeout=30) as r:(ROOT/'data'/'GPL-3.0.txt').write_bytes(r.read())
    print('Fetched and hashed 21 daily profiles (3,024 normalized measurements) with source license.')

if __name__=='__main__':main()
