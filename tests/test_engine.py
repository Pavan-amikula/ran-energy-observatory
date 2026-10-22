import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.engine import Config, Packet, compare, power_trace, simulate, traffic, validate_trace
from app.main import app

def test_arrivals_identical_and_bit_conservation():
    r=compare(Config(duration_ms=40))
    for run in r['runs'].values():
        s=run['stats']
        assert s['offered_bits']==s['delivered_bits']+s['backlog_bits']
        assert np.array(run['grid']).shape==(51,1120)
        assert 0 <= s['delivery_fairness'] <= 1
    assert len({x['stats']['offered_bits'] for x in r['runs'].values()})==1
    assert r['runs']['always_on']['grid']==r['runs']['micro_sleep']['grid']

def test_reproducibility_and_seed_changes():
    c=Config(duration_ms=20)
    assert compare(c)==compare(c)
    assert traffic(c)!=traffic(Config(duration_ms=20,seed=43))

def test_sleep_energy_integral_and_wake_cost():
    c=Config(duration_ms=20,min_gap_symbols=4)
    grid=np.zeros((14,51),int)
    p,s,n=power_trace(grid,c,True)
    # 2 entry + 11 sleeping + 1 wake, wake energy integrated exactly once.
    assert n==1 and np.sum(s==2)==11 and s[-1]==3
    expected=(3*c.active_w+11*c.sleep_w)*c.symbol_ms/1000+c.wake_mj/1000
    assert p.sum()*c.symbol_ms/1000==pytest.approx(expected)

def test_control_prevents_sleep_and_unprofitable_wake_is_rejected():
    c=Config(duration_ms=20)
    grid=np.zeros((14,51),int);grid[:,0]=-1
    _,s,n=power_trace(grid,c,True)
    assert n==0 and np.all(s==0)
    _,_,n=power_trace(np.zeros((14,51),int),Config(wake_mj=100),True)
    assert n==0

def test_zero_load_has_no_fabricated_latency():
    r=compare(Config(load=0,duration_ms=20))
    for run in r['runs'].values():
        assert run['stats']['delivered_bits']==0
        assert run['stats']['p95_latency_ms'] is None
        assert run['stats']['energy_j']>0  # mandatory signalling and idle power

def test_overload_exposes_unfinished_and_missed_packets():
    c=Config(duration_ms=40,load=1.5,scenario='overload')
    s=compare(c)['runs']['compact']['stats']
    assert s['backlog_bits']>0 and s['deadline_misses']>0

def test_no_transmission_before_arrival_and_completion_is_last_cell():
    c=Config(duration_ms=20)
    packet=Packet(0,14,3,200,500,False)
    r=simulate(c,'always_on',[packet]);g=np.array(r['grid'])
    cells=np.where(g==3)[1]
    assert cells.min()>=14
    assert r['stats']['p95_latency_ms']==round((cells.max()+1-14)*c.symbol_ms,3)

def test_horizon_censoring():
    c=Config(duration_ms=20)
    ps=[Packet(0,546,3,10000000,2000,False)]
    s=simulate(c,'compact',ps)['stats']
    assert s['censored_packets']==1 and s['deadline_misses']==0

def test_unfinished_packet_due_exactly_at_horizon_is_missed():
    c=Config(duration_ms=20)
    s=simulate(c,'compact',[Packet(0,546,3,10000000,c.symbols,False)])['stats']
    assert s['deadline_misses']==1 and s['censored_packets']==0

def test_equal_work_drain_and_measurement_derived_envelope():
    import hashlib
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    expected=json.loads((root/'data'/'provenance.json').read_text())['subset_sha256']
    assert hashlib.sha256((root/'data'/'milan_profiles.csv').read_bytes()).hexdigest()==expected
    r=compare(Config(duration_ms=80,drain_ms=40))
    assert all(v['stats']['backlog_bits']==0 for v in r['runs'].values())
    assert len({v['stats']['delivered_bits'] for v in r['runs'].values()})==1
    m=compare(Config(duration_ms=20,scenario='milan'))
    assert 'measurement-derived' in m['meta']['source']
    assert m['runs']['compact']['stats']['offered_bits']>0

def test_trace_validation_and_api():
    client=TestClient(app)
    assert client.get('/api/health').status_code==200
    assert client.post('/api/compare',json={'radio':'invalid'}).status_code==422
    assert client.post('/api/compare',json={'sleep_w':500}).status_code==422
    csv='arrival_ms,ue,bits,deadline_ms\n0,1,2400,4\n1,4,9600,15\n'
    response=client.post('/api/trace',json={'config':{'duration_ms':20},'csv':csv})
    assert response.status_code==200
    assert response.json()['runs']['compact']['stats']['offered_bits']==12000
    with pytest.raises(ValueError):validate_trace([{'arrival_ms':-1,'ue':1,'bits':2,'deadline_ms':4}],Config())

def test_external_allocation_ingestion():
    client=TestClient(app)
    frame={'source':'test-fixture','timestamp_ms':1,'grid':[[0]*51 for _ in range(14)]}
    r=client.post('/api/telemetry',json=frame)
    assert r.status_code==200 and r.json()['accepted']
    assert 'uncalibrated' in r.json()['record']['power_provenance']
    frame['grid'][0]=[7]*51
    assert client.post('/api/telemetry',json=frame).status_code==422

def test_lte_geometry():
    r=compare(Config(radio='LTE',duration_ms=20))
    g=np.array(r['runs']['always_on']['grid'])
    assert g.shape==(100,280)
    assert np.all(g[:3,::14]==-1) and np.all(g[:3,7::14]==-1)

def test_sse_replay_is_labelled():
    client=TestClient(app)
    r=client.get('/api/stream?seed=42')
    assert r.status_code==200 and 'paced simulation replay' in r.text
