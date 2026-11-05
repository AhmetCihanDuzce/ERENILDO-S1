"""Recompute paper statistics from archived tables; no solver executions.
Python 3.12 + numpy. Bootstrap percentile intervals, 50000 samples, seed 20261016.
"""
from pathlib import Path
import csv,json,math,collections,hashlib
import numpy as np
R=Path(__file__).resolve().parent
def read(n):return list(csv.DictReader((R/n).open()))
def write(n,rows):
 with (R/n).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
kp=read('COMBINED_210_PAIRS.csv');tsp=read('ALL_EXACT_TERMINALS_V27.csv');flags={(x['instance'],int(x['workers'])):x['execution_order_exception'] for x in read('ALL_MATCHED_EXACT_PAIRS_V27.csv')}
assert len(kp)==210 and len(tsp)==90
pairs=[];terminals=[]
for x in kp:
 assert x['exact']=='True'
 family=x['family'];p=int(x['p']);n=int(x['n'])
 # KP/AP provenance is an archive/run series, not an assertion of common hardware.
 cohort='KP_P09_P08' if family=='KP' and n==10 else 'KP_P07J' if family=='KP' else 'AP_P12' if n in (5,10) else 'AP_P31'
 a,b=int(x['s']),int(x['b']);F=a-b;I=a-p*F
 assert F>0 and I>=0
 if x['scalar']!='':assert int(x['scalar'])==F+I
 row=dict(family=family,p=p,n=n,instance=x['instance'],workers=int(x['workers']),standard_MILP=a,block2_MILP=b,feasible=F,infeasible=I,scalarizations=F+I,pareto=int(x['pareto']),standard_wall_s=float(x['ss']),block2_wall_s=float(x['bs']),timing_stratum=cohort,source_cohort=cohort,execution_order_exception='not_encoded_in_combined_table',counter_evidence=('F_I_reconstructed_and_checked_against_recorded_scalarizations' if x['scalar']!='' else 'F_I_scalarizations_reconstructed_from_calls_not_independently_rechecked'),provenance='COMBINED_210_PAIRS.csv')
 pairs.append(row)
groups=collections.defaultdict(dict)
for x in tsp:groups[(x['instance'],int(x['workers']))][x['method']]=x
for (ins,w),g in sorted(groups.items()):
 assert set(g)=={'standard','block2'};a,b=g['standard'],g['block2']
 for k in ['pareto','scalarizations','feasible','infeasible','instrumentation_cohort']:assert a[k]==b[k]
 assert a['exact']==b['exact']=='EXACT_QA_PASS'
 p,n=int(a['p']),int(a['n']);F,I=int(a['feasible']),int(a['infeasible'])
 assert int(a['MILP'])==p*F+I and int(b['MILP'])==(p-1)*F+I
 source=a['instrumentation_cohort'];cohort='TSP_V10' if source=='V10_NEW_ENVIRONMENT' else 'TSP_PRE_V10'
 pairs.append(dict(family='TSP',p=p,n=n,instance=ins,workers=w,standard_MILP=int(a['MILP']),block2_MILP=int(b['MILP']),feasible=F,infeasible=I,scalarizations=F+I,pareto=int(a['pareto']),standard_wall_s=float(a['wall_s']),block2_wall_s=float(b['wall_s']),timing_stratum=cohort,source_cohort=source,execution_order_exception=flags[(ins,w)],counter_evidence='recorded_F_I_scalarizations',provenance='ALL_EXACT_TERMINALS_V27.csv'))
pairs.sort(key=lambda x:(x['family'],x['p'],x['n'],x['instance'],x['workers']))
assert len(pairs)==255 and len({(x['instance'],x['workers']) for x in pairs})==255
assert len({x['instance'] for x in pairs})==85
for ins in {x['instance'] for x in pairs}:
 g=[x for x in pairs if x['instance']==ins]
 assert {x['workers'] for x in g}=={1,2,4}
 assert len({tuple(x[k] for k in ['standard_MILP','block2_MILP','feasible','infeasible','scalarizations','pareto']) for x in g})==1
for x in pairs:
 assert x['standard_wall_s']>0 and x['block2_wall_s']>0
 x['time_ratio']=x['block2_wall_s']/x['standard_wall_s']
 for method in ['standard','block2']:
  terminals.append(dict(family=x['family'],p=x['p'],n=x['n'],instance=x['instance'],workers=x['workers'],method=method,MILP=x[method+'_MILP'],wall_s=x[method+'_wall_s'],pareto=x['pareto'],scalarizations=x['scalarizations'],timing_stratum=x['timing_stratum'],source_cohort=x['source_cohort'],status='inherited_exact_QA',provenance=x['provenance']))
write('ALL_255_PAIRS.csv',pairs);write('ALL_510_TERMINAL_OBSERVATIONS.csv',terminals)
unique=[x for x in pairs if x['workers']==1];callgroups=collections.defaultdict(list)
for x in unique:callgroups[(x['family'],x['p'],x['n'])].append(x)
calls=[]
for (fam,p,n),g in sorted(callgroups.items()):
 a=sum(x['standard_MILP'] for x in g);b=sum(x['block2_MILP'] for x in g);F=sum(x['feasible'] for x in g);I=sum(x['infeasible'] for x in g)
 calls.append(dict(family=fam,p=p,n=n,benchmarks=len(g),standard=a,block2=b,saved=a-b,saving_percent=100*(a-b)/a,infeasible_share=I/(F+I),pareto_min=min(x['pareto'] for x in g),pareto_max=max(x['pareto'] for x in g)))
write('CALL_SUMMARY.csv',calls)
rng=np.random.default_rng(20261016)
def estimate(logs):
 v=np.asarray(logs);g=float(np.exp(v.mean()))
 if len(v)<3:return g,'',''
 boot=np.exp(v[rng.integers(0,len(v),size=(50000,len(v)))].mean(axis=1));lo,hi=np.quantile(boot,[.025,.975]);return g,float(lo),float(hi)
tg=collections.defaultdict(list)
for x in pairs:
 # Keep pre-V10 source series distinct; do not assume versions share a clock.
 stratum=x['source_cohort'] if x['timing_stratum']=='TSP_PRE_V10' else x['timing_stratum']
 tg[(x['family'],x['p'],x['n'],stratum,x['workers'])].append(x)
timing=[]
for (fam,p,n,c,w),g in sorted(tg.items()):
 gm,lo,hi=estimate([math.log(x['time_ratio']) for x in g])
 timing.append(dict(family=fam,p=p,n=n,cohort=c,workers=w,benchmarks=len(g),block2_faster=sum(x['time_ratio']<1 for x in g),geomean_ratio=gm,bootstrap_low=lo,bootstrap_high=hi,order_exceptions=(sum(x['execution_order_exception']=='True' for x in g) if fam=='TSP' else ''),order_metadata=('recorded_TSP_flags' if fam=='TSP' else 'not_encoded_in_combined_table')))
write('TIMING_STRATIFIED.csv',timing)
# Absolute durations are reported within the same source/worker strata as ratios.
absolute=[]
for (fam,p,n,c,w),g in sorted(tg.items()):
 for method in ['standard','block2']:
  v=np.asarray([x[method+'_wall_s'] for x in g])
  absolute.append(dict(family=fam,p=p,n=n,cohort=c,workers=w,method=method,benchmarks=len(g),median_wall_s=float(np.median(v)),min_wall_s=float(v.min()),max_wall_s=float(v.max())))
write('ABSOLUTE_TIMES_STRATIFIED.csv',absolute)
# One independent cluster per instance: average the three within-worker log ratios.
# Only rows with a single provenance stratum for the full instance are summarized.
cg=collections.defaultdict(list)
for ins in sorted({x['instance'] for x in pairs}):
 g=[x for x in pairs if x['instance']==ins];first=g[0]
 if len({x['source_cohort'] for x in g})!=1:continue
 cg[(first['family'],first['p'],first['n'],first['source_cohort'])].append(float(np.mean([math.log(x['time_ratio']) for x in g])))
cluster=[]
for (fam,p,n,c),v in sorted(cg.items()):
 gm,lo,hi=estimate(v);cluster.append(dict(family=fam,p=p,n=n,cohort=c,independent_clusters=len(v),geomean_ratio=gm,bootstrap_low=lo,bootstrap_high=hi))
write('BENCHMARK_CLUSTER_SUMMARY.csv',cluster)
# Scaling is descriptive and computed only where archived cohort labels match.
scale=[]
for x in pairs:
 if x['workers']==1:continue
 base=next(z for z in pairs if z['instance']==x['instance'] and z['workers']==1)
 if base['source_cohort']!=x['source_cohort']:continue
 for m in ['standard','block2']:
  speed=base[m+'_wall_s']/x[m+'_wall_s'];scale.append(dict(instance=x['instance'],family=x['family'],p=x['p'],n=x['n'],cohort=x['source_cohort'],workers=x['workers'],method=m,speedup=speed,efficiency=speed/x['workers']))
write('SCALING_DESCRIPTIVE.csv',scale)
# Sensitivity: omit the recorded TSP order exception.
sensitivity=[]
for w in [1,2,4]:
 g=[x for x in pairs if x['family']=='TSP' and x['p']==3 and x['workers']==w and x['execution_order_exception']!='True']
 gm,lo,hi=estimate([math.log(x['time_ratio']) for x in g]);sensitivity.append(dict(workers=w,benchmarks=len(g),geomean_ratio=gm,bootstrap_low=lo,bootstrap_high=hi))
write('TSP_N10_ORDER_SENSITIVITY.csv',sensitivity)
qa=dict(benchmarks=85,pairs=255,terminal_observations=510,design_complete=True,table_arithmetic_consistency='PASS',counter_evidence_pairs=dict(collections.Counter(x['counter_evidence'] for x in pairs)),independent_raw_counter_reverification_this_analysis=False,node_set_equality_independently_checked_this_analysis=False,scope='Table-level reconciliation; inherits prior exact Pareto QA, no fresh solver runs or full raw terminal re-QA',bootstrap=dict(seed=20261016,resamples=50000,interval='percentile 95%',minimum_benchmarks=3,analysis_status='post_hoc_exploratory_descriptive',interpretation='Conditional benchmark heterogeneity; not repeated-runtime noise or random population sampling'),calls=dict(standard=sum(x['standard_MILP'] for x in unique),block2=sum(x['block2_MILP'] for x in unique)),inputs={n:digest(R/n) for n in ['COMBINED_210_PAIRS.csv','ALL_EXACT_TERMINALS_V27.csv','ALL_MATCHED_EXACT_PAIRS_V27.csv']})
qa['calls']['saved']=qa['calls']['standard']-qa['calls']['block2'];qa['calls']['percent']=100*qa['calls']['saved']/qa['calls']['standard']
(R/'ANALYSIS_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
print('\nCALLS',calls);print('\nTIMING',timing);print('\nCLUSTER',cluster)
