"""Ridge autoregression on week-labelled Milan normalized activity profiles.

Train weeks 1–2, test week 3. One-step prediction uses only observed lags.
This predicts normalized traffic activity, not radio power or real PRB schedules.
"""
import csv
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DAYS=['mon','tue','wed','thu','fri','sat','sun']

def series(rows,week):
    return np.concatenate([[float(r[f'thp_{d}_milan13_w{week}_sid4259']) for r in rows] for d in DAYS])

def features(y):
    x=[];targets=[];indices=[]
    for i in range(6,len(y)):
        phase=(i%144)*2*np.pi/144
        x.append([1.,*y[i-6:i][::-1],np.sin(phase),np.cos(phase)])
        targets.append(y[i]);indices.append(i)
    return np.array(x),np.array(targets),np.array(indices)

def main():
    with (ROOT/'data'/'milan_profiles.csv').open() as f:rows=list(csv.DictReader(f))
    train=np.concatenate([series(rows,1),series(rows,2)]);test=series(rows,3)
    x,y,_=features(train);xt,yt,idx=features(test)
    penalty=np.eye(x.shape[1])*.1;penalty[0,0]=0
    coefficients=np.linalg.solve(x.T@x+penalty,x.T@y)
    pred=np.clip(xt@coefficients,0,1);persistence=xt[:,1]
    metrics=lambda p:{'mae':float(np.mean(abs(yt-p))),'rmse':float(np.sqrt(np.mean((yt-p)**2)))}
    summary={'task':'one-step-ahead prediction of normalized measurement-derived traffic activity; not energy prediction',
        'split':'week labels 1–2 training; week label 3 held out; no shuffled split',
        'caveat':'Published normalized profiles, not a dated raw network time series. Actual chronological week dates are not verified. Test lags use previously observed test values.',
        'train_examples':len(y),'test_examples':len(yt),'ridge_alpha':.1,'model':'six-lag ridge autoregression with daily sine/cosine features',
        'ridge':metrics(pred),'persistence':metrics(persistence),'coefficients':coefficients.tolist()}
    (ROOT/'results'/'forecast-metrics.json').write_text(json.dumps(summary,indent=2))
    with (ROOT/'results'/'forecast-predictions.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['week3_index','observed_activity','ridge_prediction','persistence_prediction']);w.writerows(zip(idx,yt,pred,persistence))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
