from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
rows=[x for x in csv.DictReader((R/'BENCHMARK_CLUSTER_SUMMARY.csv').open()) if x['bootstrap_low']!='']
fig,ax=plt.subplots(figsize=(8,5.4),layout='constrained')
ys=np.arange(len(rows))
v=np.array([float(x['geomean_ratio']) for x in rows]);lo=np.array([float(x['bootstrap_low']) for x in rows]);hi=np.array([float(x['bootstrap_high']) for x in rows])
ax.errorbar(v,ys,xerr=np.array([v-lo,hi-v]),fmt='o',color='#195b7a',ecolor='#4786a3',capsize=3)
ax.axvline(1,color='#555555',lw=1,ls='--')
ax.set_yticks(ys,[f"{x['family']}  p={x['p']}, n={x['n']}  (B={x['independent_clusters']})" for x in rows]);ax.invert_yaxis()
ax.set_xlabel('EREN–ILDO / Standard: geometric mean wall-time ratio')
ax.set_title('Benchmark-cluster summaries across 1, 2 and 4 workers',fontsize=12)
ax.grid(axis='x',alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('95% percentile bootstrap intervals; fixed benchmark panel, not runtime repetitions',fontsize=9,y=.01)
fig.savefig(R/'Figure_1_Time_Ratios.png',dpi=200,bbox_inches='tight');fig.savefig(R/'Figure_1_Time_Ratios.pdf',bbox_inches='tight')
