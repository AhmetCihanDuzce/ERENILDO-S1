import multiprocessing as mp,os,queue,time,sys,traceback
sys.path.insert(0,'src')
import run_checkpoint_multi as r

def main():
 cpus=sorted(os.sched_getaffinity(0));ctx=mp.get_context('spawn');qin=ctx.Queue();qout=ctx.Queue()
 ps=[ctx.Process(target=r.worker,args=('inputs/TSP3-40-1.json','standard',qin,qout,cpu,f'/tmp/debugw{j}.jsonl')) for j,cpu in enumerate(cpus[:4])]
 for p in ps:p.start()
 t=time.time();
 while time.time()-t<40:
  try: print('MESSAGE',qout.get(timeout=1),flush=True)
  except queue.Empty: pass
  print('ALIVE',[(p.pid,p.is_alive(),p.exitcode) for p in ps],flush=True)
  if all(not p.is_alive() for p in ps):break
 for p in ps:
  if p.is_alive():p.terminate()
  p.join()
if __name__=='__main__':main()
