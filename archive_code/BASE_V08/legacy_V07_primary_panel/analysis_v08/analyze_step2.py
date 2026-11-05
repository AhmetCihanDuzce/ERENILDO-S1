"""Frozen archived-data analysis. No solver imports or executions."""
from pathlib import Path
import json,csv,math,hashlib,collections,statistics
import numpy as np
R=Path(__file__).resolve().parent;OUT=R/'outputs';OUT.mkdir(exist_ok=True)
def read(name):return list(csv.DictReader(open(R/name,encoding='utf-8-sig')))
def write(name,rows):
 cols=list(dict.fromkeys(k for row in rows for k in row))
 with open(OUT/name,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,cols);w.writeheader();w.writerows(rows)
def load(p):return json.loads(p.read_text())
freeze=load(R/'ANALYSIS_FREEZE.json');B=freeze['bootstrap']['resamples'];seed=freeze['bootstrap']['master_seed']
def estimate(values,label):
 logs=np.log(np.array(values,dtype=float));gm=float(np.exp(logs.mean()))
 if len(logs)<3:return gm,None,None
 keyed=int.from_bytes(hashlib.sha256((str(seed)+'|'+label).encode()).digest()[:16],'little')
 rng=np.random.default_rng(keyed);boots=np.exp(logs[rng.integers(0,len(logs),size=(B,len(logs)))].mean(axis=1));lo,hi=np.quantile(boots,[.025,.975]);return gm,float(lo),float(hi)
def pairs_from(rows,source,primary):
 grouped=collections.defaultdict(dict)
 for r in rows:grouped[(r['instance'],int(r['workers']))][r['method']]=r
 pairs=[]
 for (ins,w),v in sorted(grouped.items()):
  s,b=v['standard'],v['block2'];p,n=int(s['p']),int(s['n']);exact=s['status']==b['status']=='EXACT_QA_PASS';main=ins!='TSP3-12-1'
  cohort='KP_P09_P08' if s['family']=='KP' and n==10 else s['cohort']
  r=dict(panel='main' if main else 'supplementary_n12',family=s['family'],p=p,n=n,instance=ins,workers=w,cohort=cohort,both_exact=exact,same_host=s['hostname']==b['hostname'],standard_host=s['hostname'],block2_host=b['hostname'],standard_sha=s['terminal_sha256'],block2_sha=b['terminal_sha256'],standard_wall_s=float(s['wall_s']),block2_wall_s=float(b['wall_s']),standard_solver_s=float(s['solver_time_sum_s']),block2_solver_s=float(b['solver_time_sum_s']),standard_MILP=int(s['milp_calls']),block2_MILP=int(b['milp_calls']),standard_F=int(s['feasible']),standard_I=int(s['infeasible']),block2_F=int(b['feasible']),block2_I=int(b['infeasible']),standard_pareto=int(s['pareto_count']),block2_pareto=int(b['pareto_count']),standard_scalarizations=int(s['scalarizations']),block2_scalarizations=int(b['scalarizations']),source_variant=source)
  for label,col in [('wall','wall_s'),('solver','solver_time_sum_s'),('lexwall','worker_lexwall_sum_s'),('cpu','worker_cpu_sum_s')]:r[label+'_ratio']=float(b[col])/float(s[col]) if exact else None
  if exact:
   assert r['standard_F']==r['block2_F'] and r['standard_I']==r['block2_I']
   r['call_reduction_percent']=100*(r['standard_MILP']-r['block2_MILP'])/r['standard_MILP'];r['infeasible_share']=r['standard_I']/(r['standard_F']+r['standard_I'])
   r['mean_call_solver_time_ratio']=r['solver_ratio']/(r['block2_MILP']/r['standard_MILP'])
  else:r['call_reduction_percent']=r['infeasible_share']=None
  if primary:
   for m,a in v.items():
    d=load(R/a['evidence_path']);obs={tuple(x) for x in d.get('observed_pareto_vectors',[])};ref=load(R/'evidence/oracles'/f'{ins}.json');refs={tuple(x) for x in ref.get('pareto_points',ref.get('objective_vectors',[]))}
    if exact:assert obs==refs and d['in_flight_or_queued_at_exit']==0
    if hashlib.sha256((R/a['evidence_path']).read_bytes()).hexdigest()!=a['terminal_sha256']:raise ValueError('primary SHA mismatch')
  pairs.append(r)
 return pairs
primary=read('inputs/PRIMARY_516.csv');later=read('inputs/LATEST_INDEX_516.csv')
pairs=pairs_from(primary,'publication_primary',True);latestpairs=pairs_from(later,'latest_index_sensitivity',False)
write('01_PRIMARY_258_PAIRS.csv',pairs)

# All summaries keep family, p, n, archive cohort and worker separate.
groups=collections.defaultdict(list)
for r in pairs:
 if r['both_exact']:groups[(r['panel'],r['family'],r['p'],r['n'],r['cohort'],r['workers'])].append(r)
summaries=[];sensitivity=[]
for key,g in sorted(groups.items()):
 base=dict(zip(['panel','family','p','n','cohort','workers'],key))
 for filt in ['all_archived_pairs','same_host_pairs']:
  a=g if filt=='all_archived_pairs' else [r for r in g if r['same_host']]
  if not a:continue
  row=dict(base,filter=filt,instances=len(a),excluded_pairs=len(g)-len(a),block2_faster=sum(r['wall_ratio']<1 for r in a),standard_median_s=float(np.median([r['standard_wall_s'] for r in a])),block2_median_s=float(np.median([r['block2_wall_s'] for r in a])))
  for metric in ['wall','solver','lexwall','cpu','mean_call_solver_time']:
   gm,lo,hi=estimate([r[metric+'_ratio'] for r in a],str(key)+'|'+metric)
   row[metric+'_geomean_ratio']=gm;row[metric+'_bootstrap_low']=lo;row[metric+'_bootstrap_high']=hi
  row['interpretation']='Exploratory conditional benchmark summary; same hostname does not certify equal hardware or quota.'
  summaries.append(row)
  if len(a)!=len(g):sensitivity.append(row)
write('02_TIMING_STRATIFIED.csv',summaries)

# Original fixed-panel results vs strict same-host-pair sensitivity, no sample cherry-picking.
host_comparison=[]
for key,g in sorted(groups.items()):
 if key[0]!='main':continue
 allrow=next(r for r in summaries if tuple(r[k] for k in ['panel','family','p','n','cohort','workers'])==key and r['filter']=='all_archived_pairs')
 samerow=next(r for r in summaries if tuple(r[k] for k in ['panel','family','p','n','cohort','workers'])==key and r['filter']=='same_host_pairs')
 host_comparison.append({**dict(zip(['panel','family','p','n','cohort','workers'],key)),'all_n':len(g),'same_host_n':samerow['instances'],'all_ratio':allrow['wall_geomean_ratio'],'all_low':allrow['wall_bootstrap_low'],'all_high':allrow['wall_bootstrap_high'],'same_host_ratio':samerow['wall_geomean_ratio'],'same_host_low':samerow['wall_bootstrap_low'],'same_host_high':samerow['wall_bootstrap_high'],'excluded_instances':' | '.join(r['instance'] for r in g if not r['same_host'])})
write('03_HOST_SENSITIVITY.csv',host_comparison)

joint_groups=collections.defaultdict(list);joint_eligibility=[]
for ins in sorted({r['instance'] for r in pairs if r['panel']=='main'}):
 g=[r for r in pairs if r['instance']==ins];a=g[0];cohorts={r['cohort'] for r in g};eligible={r['workers'] for r in g}=={1,2,4} and len(cohorts)==1
 joint_eligibility.append(dict(instance=ins,family=a['family'],p=a['p'],n=a['n'],eligible_single_archive_cohort=eligible,same_host_every_pair=all(r['same_host'] for r in g),cohorts=' | '.join(sorted(cohorts))))
 if eligible:
  for filt in ['all_archived_pairs','same_host_pairs']:
   if filt=='same_host_pairs' and not all(r['same_host'] for r in g):continue
   key=(a['family'],a['p'],a['n'],a['cohort'],filt)
   joint_groups[key].append({'instance':ins,'wall_ratio':math.exp(statistics.mean(math.log(r['wall_ratio']) for r in g)),'solver_ratio':math.exp(statistics.mean(math.log(r['solver_ratio']) for r in g))})
joint=[]
for key,g in sorted(joint_groups.items()):
 r=dict(zip(['family','p','n','cohort','filter'],key));r['independent_instances']=len(g)
 for metric in ['wall','solver']:
  gm,lo,hi=estimate([a[metric+'_ratio'] for a in g],'joint|'+str(key[:-1])+'|'+metric);r[metric+'_geomean_ratio']=gm;r[metric+'_bootstrap_low']=lo;r[metric+'_bootstrap_high']=hi
 joint.append(r)
write('04_JOINT_INSTANCE_CLUSTERS.csv',joint);write('05_JOINT_ELIGIBILITY.csv',joint_eligibility)

# Descriptive worker-demand distribution, no causal overhead/critical-path estimate.
workers=[];imbalance=[]
for r in primary:
 d=load(R/r['evidence_path']);w=int(r['workers']);c=d['worker_counters']
 for worker,v in c.items():workers.append(dict(instance=r['instance'],method=r['method'],workers=w,worker_id=worker,**v))
 if r['status']!='EXACT_QA_PASS' or w==1:continue
 durations=np.array([v['solver_time_sum_s'] for v in c.values()]);tasks=np.array([v['tasks'] for v in c.values()])
 assert len(durations)==w and np.isclose(durations.sum(),float(r['solver_time_sum_s']),rtol=1e-9,atol=1e-7)
 imbalance.append(dict(panel='main' if r['instance']!='TSP3-12-1' else 'supplementary_n12',instance=r['instance'],family=r['family'],p=int(r['p']),n=int(r['n']),cohort='KP_P09_P08' if r['family']=='KP' and int(r['n'])==10 else r['cohort'],workers=w,method=r['method'],solver_max_over_mean=float(durations.max()/durations.mean()),solver_cv=float(durations.std()/durations.mean()),tasks_max_over_mean=float(tasks.max()/tasks.mean()),tasks_sum=int(tasks.sum())))
write('06_WORKER_DEMAND_DISTRIBUTION.csv',imbalance);write('07_WORKER_COUNTERS.csv',workers)

# Later-repeat panel is a sensitivity comparison, never an enlargement of N.
later_summary=[]
for w in [1,2,4]:
 old=[r for r in pairs if r['family']=='TSP' and r['p']==3 and r['n']==10 and r['workers']==w]
 new=[r for r in latestpairs if r['family']=='TSP' and r['p']==3 and r['n']==10 and r['workers']==w]
 for variant,g in [('publication_primary',old),('latest_index_sensitivity',new)]:
  # Deliberately descriptive only for later mixed-cohort aggregate.
  later_summary.append(dict(workers=w,variant=variant,instances=len(g),geomean_wall_ratio=math.exp(statistics.mean(math.log(r['wall_ratio']) for r in g)),same_host_pairs=sum(r['same_host'] for r in g),cohorts=' | '.join(sorted({r['cohort'] for r in g})),note='No later mixed-cohort bootstrap or scaling claim.'))
write('08_LATER_REPEAT_SENSITIVITY.csv',later_summary)

# Main structural count: one worker level per instance, no repeated counting.
counts=[]
cg=collections.defaultdict(list)
for r in pairs:
 if r['panel']=='main' and r['workers']==1:cg[(r['family'],r['p'],r['n'])].append(r)
for key,g in sorted(cg.items()):
 s=sum(r['standard_MILP'] for r in g);b=sum(r['block2_MILP'] for r in g)
 counts.append(dict(zip(['family','p','n'],key),instances=len(g),standard_MILP=s,block2_MILP=b,saved=s-b,reduction_percent=100*(s-b)/s,infeasible_share=sum(r['standard_I'] for r in g)/sum(r['standard_scalarizations'] for r in g)))
write('09_STRUCTURAL_COUNTS.csv',counts)

qa={'status':'PASS','new_solver_runs':0,'primary_runs':len(primary),'main_pairs':sum(r['panel']=='main' for r in pairs),'main_instances':len({r['instance'] for r in pairs if r['panel']=='main'}),'supplementary_pairs':3,'exact_primary_pairs':sum(r['both_exact'] for r in pairs),'main_host_mismatch_pairs':[{'instance':r['instance'],'workers':r['workers']} for r in pairs if r['panel']=='main' and not r['same_host']],'latest_variant_host_mismatch_pairs':[{'instance':r['instance'],'workers':r['workers']} for r in latestpairs if r['panel']=='main' and not r['same_host']],'main_same_host_pairs':sum(r['panel']=='main' and r['same_host'] for r in pairs),'counts':{'standard':sum(r['standard_MILP'] for r in counts),'block2':sum(r['block2_MILP'] for r in counts)},'bootstrap':freeze['bootstrap'],'runtime':{'numpy':np.__version__},'interpretation':'No p-values, causal slopes, repeatability confidence, or unrestricted hardware scaling claims.'}
assert len(pairs)==258 and qa['main_pairs']==255 and qa['main_instances']==85 and qa['main_same_host_pairs']==253 and qa['counts']=={'standard':179507,'block2':135892}
(OUT/'ANALYSIS_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print(json.dumps(qa,ensure_ascii=False,indent=2))
