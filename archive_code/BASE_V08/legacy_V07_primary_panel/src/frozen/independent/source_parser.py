#!/usr/bin/env python3
"""Strict parser for archived Pettersson's multiobjective TSP extended-LP sources.
Only extracts objective arc weights; validates complete LP scaffold separately.
"""
import re, json, hashlib, pathlib, zipfile, csv
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
SHA=lambda b:hashlib.sha256(b).hexdigest()

def parse_lp(blob, name):
    txt=blob.decode('ascii').replace('\r\n','\n')
    found=re.search(r'TSP([34])-(\d+)-(\d+)\.lp$',name)
    if not found:raise ValueError(name)
    p,n,r=map(int,found.groups())
    assert txt.lstrip().startswith('Minimize 0\ns.t.\n')
    pieces=re.split(r'(?m)^\s*<\s*([1-4])\s*$',txt)
    assert len(pieces)>=2*p+1,(name,len(pieces))
    rhs=[int(pieces[2*k+1]) for k in range(p)]
    assert rhs==list(range(1,p+1)),(name,rhs)
    C=np.zeros((p,n,n),dtype=np.int64)
    expected={(i,j) for i in range(1,n+1) for j in range(1,n+1) if i!=j}
    rx=re.compile(r'^\s*\+?\s*(\d+)\s+X(\d+)_(\d+)\s*$', re.M)
    for k in range(p):
        body=pieces[2*k]
        if k==0:
            # skip all source assignment and MTZ rows; last of n*(n-1) U rows
            u=list(re.finditer(r'^U\d+\s+-\s+U\d+\s+\+\s+\d+\s+X\d+_\d+\s+<\s+\d+\s*$',body,re.M))
            assert len(u)==n*(n-1),(name,len(u),n)
            body=body[u[-1].end():]
        pairs=[]
        for m in rx.finditer(body):
            val,i,j=map(int,m.groups())
            assert 1<=i<=n and 1<=j<=n and i!=j,(name,i,j)
            assert C[k,i-1,j-1]==0,(name,k,i,j)
            C[k,i-1,j-1]=val
            pairs.append((i,j))
        assert set(pairs)==expected and len(pairs)==n*(n-1),(name,k,len(pairs))
        # no unparsed arc terms remain within objective body
        assert len(re.findall(r'X\d+_\d+',body))==len(pairs),(name,k)
    # further validation: exact full arc roster in binary section, all U declared general
    tail=pieces[2*p].strip()
    assert re.match(r'GENERAL\n',tail)
    general,binary=tail.split('BINARY\n')
    assert set(re.findall(r'(?m)^U(\d+)\s*$',general))==set(map(str,range(1,n+1)))
    arcs=re.findall(r'(?m)^X(\d+)_(\d+)\s*$',binary)
    assert set((int(i),int(j)) for i,j in arcs)==expected and len(arcs)==n*(n-1),(name,'binary')
    assert binary.strip().endswith('END')
    assign=pieces[0].split('s.t.\n')[1]
    eq_lines=re.findall(r'(?m)^.*=\s*1\s*$',assign)
    assert len(eq_lines)==2*n,(name,'degree',len(eq_lines))
    for line in eq_lines:
        assert len(re.findall(r'X\d+_\d+',line))==n-1
    return {'p':p,'n':n,'replicate':r,'costs':C.tolist(),'symmetric':bool(np.array_equal(C,C.transpose(0,2,1))),'input_sha256':SHA(blob)}

def main():
    out=ROOT/'source';out.mkdir(parents=True,exist_ok=True)
    entries=[]
    for p in (3,4):
        path=(ROOT/'raw'/f'TSP{p}_Tests.zip') if (ROOT/'raw'/f'TSP{p}_Tests.zip').exists() else pathlib.Path(f'/mnt/data/TSP{p}_Tests.zip')
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for name in sorted(x for x in z.namelist() if x.endswith('.lp')):
                spec=parse_lp(z.read(name),name)
                stem=pathlib.Path(name).stem
                (out/f'{stem}.json').write_text(json.dumps({'schema':'EREN-ILDO/1','problem':'TSP','n':spec['n'],'p':p,'costs':spec['costs'],'directed':True,'formulation':'mtz_binary','source_lp_sha256':spec['input_sha256'],'source_file':name},separators=(',',':'))+'\n')
                entries.append({k:spec[k] for k in ['p','n','replicate','symmetric','input_sha256']}|{'filename':name,'arc_count':spec['n']*(spec['n']-1),'model_vars':spec['n']*(spec['n']-1)+spec['n'],'zip_sha256':SHA(path.read_bytes())})
    with open(ROOT/'OFFICIAL_INSTANCE_REGISTRY.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=entries[0].keys());w.writeheader();w.writerows(entries)
    print('CERTIFIED PARSER:',len(entries),'symmetric',sum(d['symmetric'] for d in entries))
    for p in (3,4):
        print('P',p,'sizes',[(n,sum(1 for d in entries if d['p']==p and d['n']==n)) for n in sorted(set(d['n'] for d in entries if d['p']==p))])

if __name__=='__main__':main()
