#!/usr/bin/env python3
"""P35: Non-interpolated first-observed thresholds, from P34 extracted terminal/journal/checkpoint CSVs.
This does NOT infer true first-crossing times between observations.
"""
import csv, math, collections, statistics, json, pathlib
SRC=pathlib.Path(__file__).resolve().parent
DST=pathlib.Path(__file__).resolve().parent
Q=[25,50,75,90]

def read(name):
 with open(SRC/name,'r',encoding='utf-8-sig',newline='') as fh: return list(csv.DictReader(fh))
def write(name,records):
 with open(DST/name,'w',encoding='utf-8',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=list(records[0]), extrasaction='ignore');w.writeheader();w.writerows(records)
term=read('420_TERMINAL_TIMES.csv'); journal=read('ACTUAL_PROGRESS_JOURNAL_EVENTS.csv'); sched=read('ACTUAL_CHECKPOINT_OBSERVATIONS.csv')
key=lambda r:(r['instance'],int(r['workers']),r['method'])
raw=collections.defaultdict(list)
for row in journal:
 try:
  t=float(row['elapsed_active_s']);n=int(row['pareto_observed'])
 except:continue
 raw[key(row)].append((t,n,'JOURNAL',row['source']))
for row in sched:
 try:t=float(row['elapsed_s']);n=int(row['observed_pareto'])
 except:continue
 raw[key(row)].append((t,n,'SCHEDULED' if row['type']=='SCHEDULED_REAL_OBSERVATION' else 'SNAPSHOT_TERMINAL',row['source']))
long=[];wide=[];monodecs=[];pairs=[]
qa={'num_terminal':len(term),'input_journal_rows':len(journal),'input_scheduled_and_terminal_snapshots':len(sched),'actual_progress_run_count':len(raw),'monotonicity_dip_count':0,'no_imputation':True}
for row in term:
 k=key(row); T=float(row['terminal_seconds']);N=int(row['pareto_final'])
 vals=[(t,n,kind,src) for (t,n,kind,src) in raw.get(k,[]) if t>=0 and n>=0 and n<=N and (t<=T+0.25 or kind in ('SNAPSHOT_TERMINAL','JOURNAL'))]
 # A terminal observation is stamped at certified external time, ignoring end-of-write timing jitter.
 vals=[(min(t,T),n,kind,src) if n==N and ('TERMINAL' in kind or (kind=='JOURNAL' and abs(t-T)<0.5)) else (t,n,kind,src) for t,n,kind,src in vals]
 vals=[(t,n,kind,src) for t,n,kind,src in vals if t<=T+0.25]
 # Always include certified terminal, even for zero journal/cp histories.
 vals.append((T,N,'CERTIFIED_TERMINAL',row['source']))
 vals.sort(key=lambda x:(x[0],x[1],x[2]))
 # Detect count decreases only for consecutive journal observations (mixed sources may be async)
 vj=sorted([(t,n) for t,n,kind,s in vals if kind=='JOURNAL'],key=lambda x:x[0])
 for (t1,n1),(t2,n2) in zip(vj,vj[1:]):
  if n2<n1:
   qa['monotonicity_dip_count']+=1
   monodecs.append({'instance':row['instance'],'workers':int(row['workers']),'method':row['method'],'t_before':round(t1,6),'pareto_before':n1,'t_after':round(t2,6),'pareto_after':n2,'note':'Progress candidate counts can be transiently nonmonotonic'})
 unique_progress=sum(1 for t,n,kind,s in vals if t<T-0.001 and kind!='CERTIFIED_TERMINAL')
 w={'family':row['family'],'p':int(row['p']),'n':int(row['n']),'ins':int(row['ins']),'instance':row['instance'],'workers':int(row['workers']),'method':row['method'],'pareto_final':N,'exact_terminal_s':round(T,6),'actual_preterminal_events':unique_progress}
 for pct in Q:
  req=math.ceil(N*pct/100)
  hit_idx=next(i for i,(t,n,kind,s) in enumerate(vals) if n>=req)
  t,n,kind,s=vals[hit_idx]
  # Valid lower bound: latest previous observation (not necessarily immediate if same-time duplicates), or start=0.
  earlier=[(tm,c,ki,so) for tm,c,ki,so in vals[:hit_idx] if tm < t-1e-8]
  if earlier:
   lo=max(tm for tm,c,ki,so in earlier)
   prev=max((z for z in earlier if abs(z[0]-lo)<1e-8), key=lambda x:x[1]); prev_n=prev[1]
  else:lo=0.0;prev_n=0
  if t < T-0.001:
   flag='PRETERMINAL_OBSERVED'
  elif unique_progress:
   flag='TERMINAL_BOUND_WITH_PROGRESS'
  else:
   flag='TERMINAL_ONLY_NO_PROGRESS'
  # conservative interval [lo, t] -- exact first arrival unknown between observations
  later_dip=any(nn<req and ti>t+1e-9 for ti,nn,ki,s in vals)
  r={'family':row['family'],'p':int(row['p']),'n':int(row['n']),'ins':int(row['ins']),'instance':row['instance'],'workers':int(row['workers']),'method':row['method'],'threshold_pct':pct,'required_count':req,'pareto_final':N,'first_observed_at_s_upper':round(t,6),'last_prior_observation_at_s_lower':round(lo,6),'interval_width_s':round(max(0,t-lo),6),'last_prior_observed_count':prev_n,'first_observed_count':n,'first_observed_type':kind,'evidence_grade':flag,'later_fell_below_threshold':later_dip,'exact_terminal_s':round(T,6),'upper_fraction_terminal':round(t/T,6) if T>0 else None,'source_first_observed':s}
  long.append(r)
  w[f'T{pct}_upper_s']=r['first_observed_at_s_upper'];w[f'T{pct}_lower_s']=r['last_prior_observation_at_s_lower'];w[f'T{pct}_evidence']=flag
  w[f'T{pct}_later_dip']=later_dip
 wide.append(w)
write('THRESHOLD_1680_LONG.csv',long)
write('THRESHOLD_420_WIDE.csv',wide)
write('TRANSIENT_COUNT_DECREASES.csv',monodecs or [{'instance':'NONE','workers':'','method':'','t_before':'','pareto_before':'','t_after':'','pareto_after':'','note':'No dips'}])
# paired conservative thresholds
bylong={(r['instance'],r['workers'],r['method'],r['threshold_pct']):r for r in long}
for t in term:
 if t['method']!='standard':continue
 for pct in Q:
  s=bylong[(t['instance'],int(t['workers']),'standard',pct)];b=bylong[(t['instance'],int(t['workers']),'block2',pct)]
  su=s['first_observed_at_s_upper'];sl=s['last_prior_observation_at_s_lower'];bu=b['first_observed_at_s_upper'];bl=b['last_prior_observation_at_s_lower']
  if bu<sl:dom='BLOCK2_CERTAINLY_EARLIER_IN_BOUNDS'
  elif su<bl:dom='STANDARD_CERTAINLY_EARLIER_IN_BOUNDS'
  else:dom='OVERLAPPING_UNCERTAINTY_INTERVALS'
  pairs.append({'family':s['family'],'p':s['p'],'n':s['n'],'ins':s['ins'],'instance':s['instance'],'workers':s['workers'],'threshold_pct':pct,'pareto_final':s['pareto_final'],'standard_lower_s':sl,'standard_upper_s':su,'block2_lower_s':bl,'block2_upper_s':bu,'standard_evidence':s['evidence_grade'],'block2_evidence':b['evidence_grade'],'observed_upper_ratio_standard_div_block2':round(su/bu,6) if bu else None,'strict_interval_conclusion':dom,'both_preterminal_observed':s['evidence_grade']=='PRETERMINAL_OBSERVED' and b['evidence_grade']=='PRETERMINAL_OBSERVED'})
write('THRESHOLD_840_PAIRED.csv',pairs)
summary=[]
for grpkey in sorted(set((r['family'],r['p'],r['n'],r['workers'],r['method'],r['threshold_pct']) for r in long)):
 a=[r for r in long if (r['family'],r['p'],r['n'],r['workers'],r['method'],r['threshold_pct'])==grpkey]
 family,p,n,workers,method,pct=grpkey
 usable=[r for r in a if r['evidence_grade']=='PRETERMINAL_OBSERVED']
 summary.append({'family':family,'p':p,'n':n,'workers':workers,'method':method,'threshold_pct':pct,'n_benchmarks':len(a),'preterminal_observed_n':len(usable),'terminal_bound_with_progress_n':sum(r['evidence_grade']=='TERMINAL_BOUND_WITH_PROGRESS' for r in a),'terminal_only_no_progress_n':sum(r['evidence_grade']=='TERMINAL_ONLY_NO_PROGRESS' for r in a),'median_observed_upper_s_all':round(statistics.median(r['first_observed_at_s_upper'] for r in a),6),'median_width_s_all':round(statistics.median(r['interval_width_s'] for r in a),6),'median_observed_upper_s_preterminal_only':round(statistics.median(r['first_observed_at_s_upper'] for r in usable),6) if usable else '', 'count_later_dip':sum(r['later_fell_below_threshold'] for r in a)})
write('THRESHOLD_168_GROUP_SUMMARY.csv',summary)
pair_group=[]
for gkey in sorted(set((r['family'],r['p'],r['n'],r['workers'],r['threshold_pct']) for r in pairs)):
 a=[r for r in pairs if (r['family'],r['p'],r['n'],r['workers'],r['threshold_pct'])==gkey]
 family,p,n,workers,pct=gkey
 good=[r for r in a if r['both_preterminal_observed']]
 pair_group.append({'family':family,'p':p,'n':n,'workers':workers,'threshold_pct':pct,'total_pairs':len(a),'both_preterminal_observed':len(good),'definitely_block2_earlier':sum(r['strict_interval_conclusion']=='BLOCK2_CERTAINLY_EARLIER_IN_BOUNDS' for r in a),'definitely_standard_earlier':sum(r['strict_interval_conclusion']=='STANDARD_CERTAINLY_EARLIER_IN_BOUNDS' for r in a),'uncertainty_intervals_overlap':sum(r['strict_interval_conclusion']=='OVERLAPPING_UNCERTAINTY_INTERVALS' for r in a),'median_observed_upper_ratio_both_preterminal':round(statistics.median(r['observed_upper_ratio_standard_div_block2'] for r in good),6) if good else ''})
write('THRESHOLD_84_PAIRED_GROUP_SUMMARY.csv',pair_group)
qa['num_threshold_records']=len(long);qa['num_pair_thresholds']=len(pairs);qa['num_preterminal_observed']=sum(x['evidence_grade']=='PRETERMINAL_OBSERVED' for x in long);qa['num_terminal_only_no_progress']=sum(x['evidence_grade']=='TERMINAL_ONLY_NO_PROGRESS' for x in long);qa['num_terminal_bound_with_progress']=sum(x['evidence_grade']=='TERMINAL_BOUND_WITH_PROGRESS' for x in long);qa['num_later_dip_thresholds']=sum(x['later_fell_below_threshold'] for x in long);qa['num_total_basecases']=len(set(x['instance'] for x in term))
assert len(long)==1680 and len(wide)==420 and len(pairs)==840
assert all(float(r['first_observed_at_s_upper']) <= float(r['exact_terminal_s'])+1e-6 for r in long)
assert all(int(r['first_observed_count'])>=int(r['required_count']) for r in long)
assert all(r['last_prior_observation_at_s_lower']<=r['first_observed_at_s_upper'] for r in long)
(DST/'QA_THRESHOLD.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(qa,indent=2,ensure_ascii=False))
print('PAIR summary examples',pair_group[-5:])
