"""Common observation window with final arrival-free drain; sensitivity evidence."""
import csv
import json
from pathlib import Path
from app.engine import Config,compare
ROOT=Path(__file__).resolve().parents[1]

def main():
    cases=[]
    for seed in [11,22,33,44,55]:
        r=compare(Config(drain_ms=40,seed=seed))
        stats={p:v['stats'] for p,v in r['runs'].items()}
        assert all(v['backlog_bits']==0 for v in stats.values()),'Unequal work: drain insufficient'
        assert len({v['delivered_bits'] for v in stats.values()})==1
        cases.append({'seed':seed,'stats':stats})
    (ROOT/'results'/'equal-work.json').write_text(json.dumps({'description':'160 ms common horizon; packet arrivals stop at 120 ms; five seeds, NR bursty load 0.28. All policies must finish exactly the same payload.','cases':cases},indent=2))
    sensitivity=[]
    for sleep in [20,45,90,150]:
        for wake in [.0,.15,2.0]:
            r=compare(Config(drain_ms=40,sleep_w=sleep,wake_mj=wake))
            s=r['runs']['compact']['stats']
            sensitivity.append({'sleep_w':sleep,'wake_mj':wake,**s})
    with (ROOT/'results'/'sensitivity.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(sensitivity[0]));w.writeheader();w.writerows(sensitivity)
    print(json.dumps([{'seed':c['seed'],'saving_pct':c['stats']['compact']['saving_pct'],'delivered_bits':c['stats']['compact']['delivered_bits']} for c in cases]))

if __name__=='__main__':main()
