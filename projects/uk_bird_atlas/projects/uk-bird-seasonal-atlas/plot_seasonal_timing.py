"""Seasonal timing chart: python plot_seasonal_timing.py national_monthly_rate.csv figures/seasonal_timing.png"""
import sys, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
src, out = sys.argv[1], sys.argv[2]
df = pd.read_csv(src).set_index("common")
df.columns = [int(c) for c in df.columns]
groups = [("Summer visitors", ["Swift","Swallow","House Martin","Cuckoo","Willow Warbler"]),
          ("Passage migrant", ["Wheatear"]),
          ("Winter visitors", ["Redwing","Fieldfare","Pink-footed Goose","Whooper Swan"]),
          ("Resident (control)", ["Robin (resident control)"])]
order = [s for _, ss in groups for s in ss]
d = df.loc[order]
rel = d.div(d.max(axis=1), axis=0)
cmap = LinearSegmentedColormap.from_list("b", ["#f7f9fc","#cde2fb","#86b6ef","#3987e5","#1c5cab","#0d366b"])
ink, muted = "#1f1f1f", "#6b6b6b"
fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=150)
gaps, y, ys = [], 0, []
for gi, (g, ss) in enumerate(groups):
    for s in ss:
        ys.append(y); y += 1
    y += 0.9
for yy, s in zip(ys, order):
    for m in range(12):
        ax.add_patch(plt.Rectangle((m+0.04, yy+0.04), 0.92, 0.92, color=cmap(rel.loc[s, m+1]), lw=0))
    ax.text(12.25, yy+0.5, f"{d.loc[s].max():.0%}", va="center", fontsize=8.5, color=muted)
ax.set_xlim(0, 13.2); ax.set_ylim(y-0.5, -0.9)
ax.set_xticks(np.arange(12)+0.5); ax.set_xticklabels("J F M A M J J A S O N D".split(), fontsize=9, color=ink)
ax.xaxis.tick_top(); ax.tick_params(length=0)
ax.set_yticks([yy+0.5 for yy in ys]); ax.set_yticklabels([s.replace(" (resident control)","") for s in order], fontsize=9.5, color=ink)
gy = 0
for g, ss in groups:
    ax.text(-0.1, gy-0.12, g.upper(), fontsize=7.5, color=muted, ha="right", va="bottom", weight="bold", transform=ax.transData)
    gy += len(ss) + 0.9
ax.text(12.25, -0.9, "peak", fontsize=8, color=muted, va="bottom")
for s in ax.spines.values(): s.set_visible(False)
fig.text(0.02, 0.965, "When each species is reported across the UK", fontsize=13, weight="bold", color=ink)
fig.text(0.02, 0.925, "Monthly reporting rate as a share of each species' own peak month (right: peak rate). eBird via GBIF, 2015-2025.",
         fontsize=8.5, color=muted)
cax = fig.add_axes([0.70, 0.04, 0.22, 0.025]); cax.imshow(np.linspace(0,1,256)[None,:], aspect="auto", cmap=cmap)
cax.set_yticks([]); cax.set_xticks([0,255]); cax.set_xticklabels(["0","peak"], fontsize=8, color=muted); cax.tick_params(length=0)
for s in cax.spines.values(): s.set_visible(False)
fig.subplots_adjust(left=0.2, right=0.97, top=0.84, bottom=0.1)
fig.savefig(out, facecolor="white")
