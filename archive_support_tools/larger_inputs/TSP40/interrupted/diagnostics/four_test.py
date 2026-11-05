from pathlib import Path
import sys,os
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import run_checkpoint_multi as r
def main():
 x=r.run('inputs/TSP3-40-1.json','standard',2,(2,),str(Path(__file__).resolve().parent/'runs'/'w4_test'),4,qa=True)
 print(x)
if __name__=='__main__': main()
