from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parent
read=lambda n:list(csv.DictReader(open(R/"outputs"/n,encoding="utf-8-sig")))
rows=[r for r in read("01_PRIMARY_258_PAIRS.csv") if r["panel"]=="main"]
colors={"AP":"#2377A4","KP":"#D17B26","TSP":"#238B68"}; marks={"AP":"o","KP":"s","TSP":"^"}
for kind in ["calls","solver"]:
 fig,axes=plt.subplots(1,3,figsize=(10,4.5),sharex=True,sharey=True)
 for ax,w in zip(axes,[1,2,4]):
  for fam in colors:
   g=[r for r in rows if r["family"]==fam and int(r["workers"])==w]
   x=[float(r["call_reduction_percent"] if kind=="calls" else r["solver_ratio"]) for r in g]
   y=[float(r["wall_ratio"]) for r in g]
   ax.scatter(x,y,c=colors[fam],marker=marks[fam],s=36,alpha=.8,edgecolors="white",linewidths=.4,label=fam)
  ax.set_title(f"{w} worker" if w==1 else f"{w} workers");ax.set_yscale("log");ax.axhline(1,color="#555555",ls="--",lw=1);ax.grid(alpha=.15)
  if kind=="calls":ax.set_xlim(14,35);ax.set_xlabel("MILP call reduction (%)")
  else:
   vals=[float(r[k]) for r in rows for k in ["solver_ratio","wall_ratio"]];lo=min(vals)*.9;hi=max(vals)*1.1
   ax.set_xscale("log");ax.set_xlim(lo,hi);ax.set_ylim(lo,hi);ax.plot([lo,hi],[lo,hi],color="#999999",lw=.8);ax.axvline(1,color="#555555",lw=.8,ls="--");ax.set_xlabel("Solver-time ratio")
 axes[0].set_ylabel("Elapsed-time ratio")
 fig.legend(*axes[0].get_legend_handles_labels(),ncol=3,loc="lower center",bbox_to_anchor=(.5,.005),frameon=False)
 fig.subplots_adjust(left=.09,right=.995,top=.9,bottom=.25,wspace=.13)
 fig.savefig(R/f"Figure_{kind}_EN.png",dpi=300,bbox_inches="tight");plt.close(fig)
joint=read("04_JOINT_INSTANCE_CLUSTERS.csv");keys=sorted({(r["family"],int(r["p"]),int(r["n"]),r["cohort"]) for r in joint if r["wall_bootstrap_low"]})
fig,ax=plt.subplots(figsize=(7,3.4))
for y,key in enumerate(keys):
 r=next(r for r in joint if (r["family"],int(r["p"]),int(r["n"]),r["cohort"])==key and r["filter"]=="all_archived_pairs")
 v,lo,hi=map(float,[r["wall_geomean_ratio"],r["wall_bootstrap_low"],r["wall_bootstrap_high"]]);ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt="o",color="#2377A4",capsize=3,ms=4)
 ax.set_yticks(range(len(keys)),[f"{k[0]} p={k[1]}, n={k[2]}" for k in keys]);ax.invert_yaxis();ax.axvline(1,ls="--",color="#555555",lw=.9);ax.grid(axis="x",alpha=.17);ax.set_xlabel("EREN–ILDO / Standard joint geometric runtime ratio")
fig.subplots_adjust(left=.31,right=.98,top=.98,bottom=.2);fig.savefig(R/"Figure_joint_EN.png",dpi=300,bbox_inches="tight")
