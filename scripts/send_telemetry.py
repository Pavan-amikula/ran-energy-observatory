"""Exercise external ingestion with simulated allocation frames (not SDR data)."""
import argparse
import json
import time
from urllib.request import Request,urlopen
from app.engine import Config,compare

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8000');args=parser.parse_args()
    r=compare(Config());grid=r['runs']['compact']['grid']
    for t in range(0,len(grid[0]),14):
        frame={'source':'simulated-adapter-demo','timestamp_ms':t*r['meta']['symbol_ms'],'radio':'NR',
            'grid':[[grid[f][s] for f in range(r['meta']['prbs'])] for s in range(t,t+14)]}
        req=Request(args.url+'/api/telemetry',data=json.dumps(frame).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req) as response:response.read()
        time.sleep(.08)
    print('Allocation frames sent. Dashboard: Connect telemetry.')

if __name__=='__main__':main()
