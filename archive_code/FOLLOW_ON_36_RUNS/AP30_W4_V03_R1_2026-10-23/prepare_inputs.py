from pathlib import Path
import ast,hashlib,json,zipfile,shutil,sys,os,platform
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
import run_checkpoint_multi as runner
import numpy as np,scipy

def main():
 for d in ['inputs','raw','runs','logs','audit']:(ROOT/d).mkdir(exist_ok=True)
 source=ROOT/'raw/ap.zip'
 if not source.exists():shutil.copyfile(ROOT.parent/'ap30_source/ap.zip',source)
 member='AP/AP_p-3_n-30_ins-1.dat'
 with zipfile.ZipFile(source) as z: raw=z.read(member)
 (ROOT/'raw/AP_p-3_n-30_ins-1.dat').write_bytes(raw)
 lines=raw.decode().splitlines();p,n=map(int,lines[:2]);costs=ast.literal_eval('\n'.join(lines[2:]));assert np.asarray(costs).shape==(3,30,30)
 source_info={'source_url':'https://raw.githubusercontent.com/srplsyn/MOOLibrary/master/ap.zip','source_member':member,'archive_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'raw_dat_sha256':hashlib.sha256(raw).hexdigest()}
 for objectives in (3,4):
  cs=costs.copy();origin='LITERATURE_BENCHMARK';generation=None
  if objectives==4:
   seed=2026102301;cs=cs+[np.random.Generator(np.random.PCG64(seed)).integers(1,21,size=(30,30),dtype=np.int64).tolist()]
   origin='SYNTHETIC_DERIVED_OBJECTIVE_EXTENSION';generation={'seed':seed,'generator':'numpy.random.Generator(PCG64(seed)).integers(1,21,size=(30,30),dtype=int64)','numpy':np.__version__,'range_inclusive':[1,20]}
  data={'problem':'AP','n':30,'p':objectives,'instance':1,'costs':cs,'objective_sense':'minimize','input_origin':origin}
  f=ROOT/'inputs'/f'AP_p{objectives}_n30_i01.json';f.write_text(json.dumps(data,indent=2)+'\n')
  prov={**source_info,'input_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'input_origin':origin,'created_before_performance_run':True,'generation':generation,'relationship':'Official three-objective benchmark, unchanged' if objectives==3 else 'Objectives 1-3 exactly equal the official p=3 n=30 i=1 input; objective 4 is a synthetic independent integer-cost matrix following the earlier AP20/AP25 extension convention.'}
  f.with_suffix('.provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
  P,d=runner.load(f);w=np.eye(30,dtype=int).reshape(-1);y=runner.validate_witness(P,d,w)
  (ROOT/'audit'/f'PREFLIGHT_p{objectives}.json').write_text(json.dumps({'status':'PASS','variables':P.n,'objectives':P.p,'equality_constraints':60,'identity_assignment_objectives':list(map(int,y)),'input_sha256':prov['input_sha256']},indent=2)+'\n')
 env={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'allowed_cpus':sorted(os.sched_getaffinity(0)),'cpu_quota':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_limit':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').glob('*.py')}}
 (ROOT/'ENVIRONMENT.json').write_text(json.dumps(env,indent=2)+'\n')
 plan={'family':'AP','n':30,'objective_counts':[3,4],'workers':4,'methods':['standard','block2'],'budget_s':1200,'checkpoints_s':[300,600,900,1200],'threads_per_worker':1,'order':[[3,'standard'],[3,'block2'],[4,'standard'],[4,'block2']],'authorization':'User requested AP30 using both methods with four workers; objectives follow existing 3/4-objective panel.','four_objective_input_origin':'SYNTHETIC_DERIVED_OBJECTIVE_EXTENSION','protocol':'V03_R1_1200S'}
 (ROOT/'RUN_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'preflight':'PASS','inputs':[3,4],'workers':4,'budget':1200,'source_sha256':source_info['archive_sha256']}))
if __name__=='__main__':main()
