"""Paired seeded experiments; write complete per-run evidence, not best-case only."""
import csv
import json
import statistics
from pathlib import Path
from app.engine import Config, compare

ROOT=Path(__file__).resolve().parents[1]

def main():
    records=[]
    for radio in ['NR','LTE']:
        for profile in ['bursty','steady','overload']:
            for load in [.1,.28,.65]:
                for seed in [11,22,33,44,55]:
                    c=Config(radio=radio,scenario=profile,load=load,seed=seed)
                    r=compare(c)
                    for p,run in r['runs'].items():
                        records.append(dict(radio=radio,profile=profile,load=load,seed=seed,policy=p,**run['stats']))
    out=ROOT/'results';out.mkdir(exist_ok=True)
    with (out/'benchmark.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    groups=[]
    for radio in ['NR','LTE']:
        for profile in ['bursty','steady','overload']:
            for load in [.1,.28,.65]:
                group=[r for r in records if r['radio']==radio and r['profile']==profile and r['load']==load and r['policy']=='compact']
                vals=[r['saving_pct'] for r in group]
                groups.append(dict(radio=radio,profile=profile,load=load,n=len(vals),saving_mean_pct=round(statistics.mean(vals),2),
                    saving_min_pct=min(vals),saving_max_pct=max(vals),saving_sd_pct=round(statistics.stdev(vals),2),
                    p95_latency_mean_ms=round(statistics.mean(r['p95_latency_ms'] for r in group if r['p95_latency_ms'] is not None),3),
                    deadline_miss_mean_pct=round(statistics.mean(r['deadline_miss_pct'] for r in group),3),
                    backlog_mean_bits=round(statistics.mean(r['backlog_bits'] for r in group))))
    (out/'summary.json').write_text(json.dumps({'design':'90 paired configurations, 270 policy evaluations; five fixed seeds per group. Descriptive seed ranges, not field confidence bounds.','groups':groups},indent=2))
    example=compare(Config())
    (out/'example.json').write_text(json.dumps(example))
    print(json.dumps(groups,indent=2))

if __name__=='__main__':main()
