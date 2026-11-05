"""Sequential KP30 p3/p4 worker panel, immutable common solver sources."""
import hashlib
import itertools
import json
import pathlib
import sys
import time
import zipfile
import numpy as np
from run_checkpoint import ROOT, run, save, load

OUT = ROOT.parents[1] / 'output/EREN_ILDO_KP_N30_P3_P4_ALL_WORKERS_V03_2026-10-19.zip'


def nd(points):
    a = sorted(set(map(tuple, points)))
    return [y for y in a if not any(z != y and all(u <= v for u, v in zip(z, y)) for z in a)]


def pack():
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp') and p.name != 'SHA256_MANIFEST.json']
    save(ROOT / 'SHA256_MANIFEST.json', {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    temp = OUT.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files + [ROOT / 'SHA256_MANIFEST.json']):
            z.write(p, pathlib.Path(ROOT.name) / p.relative_to(ROOT))
    temp.replace(OUT)


def verify_small():
    report = []
    for p, instance in [(3, 'KP_n30_p3_i5'), (4, 'KP_n30_p4_i1')]:
        d = json.loads((ROOT / 'inputs' / (instance + '.json')).read_text())
        d['n'] = 10
        d['weights'] = d['weights'][:10]
        d['profits'] = [row[:10] for row in d['profits']]
        d['capacity'] = sum(d['weights']) // 2
        ip = ROOT / 'qa' / f'small_p{p}_n10.json'
        save(ip, d)
        P, _ = load(ip)
        ref = nd(tuple(map(int, P.C @ np.array(x))) for x in itertools.product([0, 1], repeat=10) if np.array(d['weights']) @ x <= d['capacity'])
        for w in [1, 2, 4]:
            for m in ['standard', 'block2']:
                prefix = ROOT / 'qa' / f'p{p}_w{w}_{m}'
                terminal = prefix.with_suffix('.terminal.json')
                r = json.loads(terminal.read_text()) if terminal.exists() else run(ip, m, budget=30, deadlines=(1, 10, 30), prefix=prefix, workers=w)
                assert r['status'] == 'SEARCH_COMPLETED', r.get('error')
                assert sorted(map(tuple, r['points_minimization'])) == ref
                for cp in r['checkpoints']:
                    assert sorted(cp['points_minimization']) == sorted(e['y_min'] for e in r['accepted_points_with_witnesses'] if e['accepted_elapsed_s'] <= cp['checkpoint_s'])
                report.append({'p': p, 'workers': w, 'method': m, 'reference_points': len(ref), 'status': 'PASS'})
    save(ROOT / 'qa/QA_SUMMARY.json', {'status': 'PASS', 'reference': 'independent exhaustive enumeration of all 1024 binary vectors, n10 slices for p3/p4', 'checks': report})


def main():
    manifest = json.loads((ROOT / 'INPUT_AND_RUN_MANIFEST.json').read_text())
    manifest['status'] = 'QA_RUNNING'
    save(ROOT / 'INPUT_AND_RUN_MANIFEST.json', manifest)
    pack()
    verify_small()
    manifest['status'] = 'RUNNING'
    manifest['start_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    save(ROOT / 'INPUT_AND_RUN_MANIFEST.json', manifest)
    pack()
    for p, instance in [(3, 'KP_n30_p3_i5'), (4, 'KP_n30_p4_i1')]:
        for w in [1, 2, 4]:
            for m in ['standard', 'block2']:
                name = f'p{p}_w{w}_{m}'
                print('START', name, flush=True)
                manifest['current_cell'] = name
                save(ROOT / 'INPUT_AND_RUN_MANIFEST.json', manifest)
                prefix = ROOT / 'runs' / name
                terminal = prefix.with_suffix('.terminal.json')
                r = json.loads(terminal.read_text()) if terminal.exists() else run(ROOT / 'inputs' / (instance + '.json'), m, prefix=prefix, workers=w)
                pack()
                if r['status'] == 'ERROR':
                    raise RuntimeError(r['error'])
    manifest['status'] = 'PERFORMANCE_RUNS_FINISHED'
    save(ROOT / 'INPUT_AND_RUN_MANIFEST.json', manifest)
    pack()
    print('ALL KP30 RUNS FINISHED', flush=True)


if __name__ == '__main__':
    main()
