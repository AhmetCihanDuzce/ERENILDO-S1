#!/usr/bin/env python3
"""Publication entry point. Archived results remain immutable; outputs use --out."""
from pathlib import Path
import argparse, csv, gzip, hashlib, json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
LEGACY = Path('BASE_V08/legacy_V07_primary_panel')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_source(row, results):
    root = ROOT if row['repository'] == 'S1' else results
    data = (root / row['path']).read_bytes()
    if row['compression'] == 'gzip':
        data = gzip.decompress(data)
    if sha(data) != row['uncompressed_sha256']:
        raise ValueError('Source checksum mismatch: ' + row['path'])
    return data

def stage(results, out):
    target = out / 'staged_snapshot'
    rows = list(csv.DictReader((ROOT/'provenance/code_snapshot_index.csv').open(encoding='utf-8-sig')))
    for row in rows:
        data = read_source(row, results)
        path = target/row['relative_path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return target / LEGACY

def execute(args, cwd=None):
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['verify','analyze','test','prepare','run'])
    p.add_argument('--results', type=Path, default=ROOT.parent/'Supplementary_S2')
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--instance')
    p.add_argument('--input', type=Path)
    p.add_argument('--method', choices=['standard','eren-ildo','block2'], default='standard')
    p.add_argument('--workers', type=int, choices=[1,2,4], default=1)
    p.add_argument('--budget', type=float, default=1200)
    p.add_argument('--checkpoints', default='300,600,900,1200')
    p.add_argument('--execute', action='store_true', help='Execute a prepared original-panel run')
    p.add_argument('--smoke', action='store_true', help='Also execute end-to-end software regressions')
    p.add_argument('--figures', action='store_true')
    p.add_argument('--qa', action='store_true', help='Allow a custom software-test budget; exclude from benchmark timing')
    a = p.parse_args(); results=a.results.resolve(); out=a.out.resolve()
    if out.exists():
        p.error('--out must be a new directory, to preserve earlier records')
    if out == ROOT or ROOT in out.parents or out == results or results in out.parents:
        p.error('--out must be outside both publication repositories')
    out.mkdir(parents=True)
    method='block2' if a.method=='eren-ildo' else a.method
    if a.action == 'run':
        if a.budget <= 0: p.error('--budget must be positive')
        inp=a.input.resolve() if a.input else None
        if inp is None:
            rows=list(csv.DictReader((results/'tables/input_registry.csv').open(encoding='utf-8-sig')))
            matches=[r for r in rows if r['instance']==a.instance]
            if len(matches)!=1: p.error('Provide an unambiguous --instance from input_registry.csv, or --input JSON')
            r=matches[0];data=(results/r['path']).read_bytes()
            if r['compression']=='gzip': data=gzip.decompress(data)
            if sha(data)!=r['input_sha256']: raise ValueError('Input checksum mismatch')
            inp=out/(Path(r['instance']).name+'.json');inp.write_bytes(data)
        execute([sys.executable,ROOT/'src/run_checkpoint_multi.py','--input',inp,'--method',method,
                 '--workers',a.workers,'--budget',a.budget,'--checkpoints',a.checkpoints,'--prefix',out/'run']+(['--qa'] if a.qa else []))
        return
    if a.action == 'verify':
        checks={}
        for name,root in [('S1',ROOT),('S2',results)]:
            manifest=json.loads((root/'MANIFEST_SHA256.json').read_text())
            for rel,h in manifest.items():
                if sha((root/rel).read_bytes())!=h: raise ValueError('Package checksum mismatch: '+name+'/'+rel)
            checks[name+'_files']=len(manifest)
        rows=list(csv.DictReader((results/'provenance/source_file_index.csv').open(encoding='utf-8-sig')))
        for row in rows:read_source(row,results)
        checks['source_records_verified']=len(rows)
        checks['archived_publication_audit']=json.loads((results/'provenance/publication_audit.json').read_text())
        (out/'package_verification.json').write_text(json.dumps(checks,indent=2))
        execute([sys.executable,ROOT/'audit_results.py','--results',results,'--out',out/'all_primary_records_verification.json'])
        base=stage(results,out)
        execute([sys.executable,base/'scripts/verify_release.py','--root',base,'--report',out/'main_panel_verification.json'])
        return
    base=stage(results,out)
    if a.action == 'analyze':
        analysis=base/'analysis_v08'
        execute([sys.executable,analysis/'analyze_step2.py'])
        generated=analysis/'outputs'
        for expected in (analysis/'expected_outputs').glob('*.csv'):
            if (generated/expected.name).read_bytes()!=expected.read_bytes():
                raise ValueError('Analysis differs: '+expected.name)
        shutil.copytree(generated,out/'analysis')
        if a.figures:
            execute([sys.executable,analysis/'plot_figures_en.py'])
            (out/'figures').mkdir()
            for fig in analysis.glob('Figure_*_EN.png'): shutil.copyfile(fig,out/'figures'/fig.name)
        print('PASS: all nine analysis CSV files reproduce exactly.')
    elif a.action == 'test':
        cmd=[sys.executable,base/'scripts/validate_software.py','--out',out/'software_validation']
        if a.smoke: cmd.append('--smoke')
        execute(cmd)
    elif a.action == 'prepare':
        if not a.instance: p.error('prepare requires --instance')
        execute([sys.executable,base/'scripts/prepare_validated_run.py','--instance',a.instance,
                 '--workers',a.workers,'--method',method,'--out',out/'prepared_run',
                 '--label','PUBLICATION_REPRODUCTION','--execute' if a.execute else '--stage-only'])

if __name__=='__main__':
    main()
