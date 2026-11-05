from pathlib import Path
import subprocess, sys, json, time, csv, hashlib
root=Path(__file__).resolve().parent
items=[]
for p in (3,4):
    inp=root/'inputs'/f'TSP{p}-20-1.json'
    for w in (1,2,4):
        for method in ('standard','block2'):
            prefix=root/'runs'/f'TSP{p}-20-1_w{w}_{method}'
            log=root/'logs'/f'{prefix.name}.log'
            audit=root/'audits'/f'{prefix.name}.json'
            start=time.time()
            cmd=[sys.executable,str(root/'src'/'run_checkpoint_multi.py'),'--input',str(inp),'--method',method,'--budget','1200','--checkpoints','300,600,900,1200','--prefix',str(prefix),'--workers',str(w)]
            print('START',prefix.name,flush=True)
            with log.open('w') as f:
                proc=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
            elapsed=time.time()-start
            terminal=prefix.with_suffix('.terminal.json')
            entry={'instance':f'TSP{p}-20-1','p':p,'workers':w,'method':method,'prefix':str(prefix.relative_to(root)),'returncode':proc.returncode,'wall_elapsed_s':elapsed,'log':str(log.relative_to(root))}
            if terminal.exists():
                t=json.loads(terminal.read_text()); entry.update(status=t.get('status'),elapsed_s=t.get('elapsed_s'),shutdown_elapsed_s=t.get('shutdown_elapsed_s'),points=len(t.get('accepted_points_with_witnesses',[])))
                acmd=[sys.executable,str(root/'validate_run_multi.py'),'--prefix',str(prefix),'--input',str(inp),'--output',str(audit)]
                with (root/'logs'/f'{prefix.name}.audit.log').open('w') as f: v=subprocess.run(acmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
                entry['audit_returncode']=v.returncode
                if audit.exists():entry['audit']=json.loads(audit.read_text()).get('audit')
            else:
                entry['status']='NO_TERMINAL_RECORD'
            items.append(entry)
            (root/'batch_progress.json').write_text(json.dumps(items,indent=2)+'\n')
            print('DONE',json.dumps(entry,sort_keys=True),flush=True)
print('BATCH_COMPLETE',len(items),flush=True)
