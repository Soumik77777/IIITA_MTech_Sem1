import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
OUT=''
df=pd.read_csv('run_table.csv')
S,M='Single agent','Multi-agent debate'
C={S:'#2a78d6',M:'#eb6834'}
INK,INK2,GRID,SURF='#0b0b0b','#52514e','#e4e3df','#fcfcfb'
plt.rcParams.update({'font.size':10,'axes.edgecolor':GRID,'axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,
 'axes.facecolor':SURF,'figure.facecolor':SURF,'axes.spines.top':False,'axes.spines.right':False,'axes.titlesize':11,'axes.titleweight':'bold','axes.titlecolor':INK})
dims=['Novelty','Significance','Feasibility','Testability']
d1=df[df.dataset=='D01']
rng=np.random.default_rng(3)
def legend(fig,y=0.98):
    h=[Patch(color=C[S],label=f'Single agent (n={ (d1["mode"]==S).sum()} runs)'),Patch(color=C[M],label=f'Multi-agent debate (n={(d1["mode"]==M).sum()} runs)'),
       Line2D([],[],marker='o',ls='',mfc='none',mec=INK2,label='individual run')]
    fig.legend(handles=h,loc='upper right',ncol=3,frameon=False,bbox_to_anchor=(0.99,y),fontsize=9)
def bars(ax,x,vals_by_mode,w=0.36,fmt='{:.2f}',lab=True):
    for i,m in enumerate([S,M]):
        v=vals_by_mode[m]
        if len(v)==0: continue
        mu=np.mean(v); sd=np.std(v,ddof=1) if len(v)>1 else 0
        xi=x+(i-0.5)*w
        ax.bar(xi,mu,w-0.03,color=C[m],zorder=2)
        if sd: ax.errorbar(xi,mu,sd,color=INK,capsize=3,lw=1,zorder=3)
        ax.scatter(xi+rng.uniform(-0.07,0.07,len(v)),v,s=22,facecolor=SURF,edgecolor=INK,lw=0.9,zorder=4)
        if lab: ax.text(xi,0.02,fmt.format(mu),ha='center',va='bottom',fontsize=9,color='white',fontweight='bold',zorder=5,
                         transform=ax.get_xaxis_transform())
def style(ax):
    ax.grid(axis='y',color=GRID,lw=0.7,zorder=0); ax.set_axisbelow(True)

# ---------- Fig 1: cost ----------
fig,axs=plt.subplots(1,3,figsize=(11,4.2))
for ax,(col,ttl,scale,f) in zip(axs,[('tokens','Total tokens per run (thousands)',1e3,'{:.0f}'),('calls','API calls per run',1,'{:.1f}'),('out','Output tokens per run (thousands)',1e3,'{:.0f}')]):
    bars(ax,0,{m:d1[d1['mode']==m][col].values/scale for m in (S,M)},w=0.7,fmt=f)
    ax.set_title(ttl); ax.set_xticks([]); ax.set_xlim(-0.6,0.6); style(ax)
    ax.margins(y=0.15)
fig.suptitle('Cost: debate uses ~2.3× the tokens of a single agent (same corpus, D01)',x=0.01,ha='left',fontweight='bold',fontsize=12.5,color=INK)
legend(fig,0.93); fig.tight_layout(rect=(0,0,1,0.88))
fig.text(0.01,0.005,'Bars = mean across runs, whiskers = ±1 SD, dots = individual runs. Cost proxy = API tokens (no price set in config). Total tokens include hidden "thinking" tokens in some runs.',fontsize=8,color=INK2)
fig.savefig(OUT+'fig1_cost.png',dpi=200); plt.close(fig)

# ---------- Fig 2: quality per dimension ----------
fig,axs=plt.subplots(1,2,figsize=(12,4.6),sharey=True)
for ax,(pre,ttl) in zip(axs,[('gap','Research gaps'),('hyp','Hypotheses')]):
    for k,dn in enumerate(dims+['Overall']):
        col=f'{pre}_{"overall" if dn=="Overall" else dn}'
        bars(ax,k,{m:d1[d1['mode']==m][col].values for m in (S,M)})
    ax.set_xticks(range(5)); ax.set_xticklabels(dims+['Overall']); ax.set_title(ttl); style(ax)
    ax.set_ylim(0,5.2); ax.axvline(3.5,color=GRID,lw=0.8)
axs[0].set_ylabel('Mean score across 5 LLM evaluators (1–5)')
fig.suptitle('Quality: debate vs single agent, by evaluation dimension (D01 runs)',x=0.01,ha='left',fontweight='bold',fontsize=12.5,color=INK)
legend(fig,0.93); fig.tight_layout(rect=(0,0.03,1,0.88))
fig.text(0.01,0.005,'Bars = mean of run means; whiskers = ±1 SD across runs; dots = runs. Overlapping dots/whiskers mean the difference is within run-to-run noise.',fontsize=8,color=INK2)
fig.savefig(OUT+'fig2_quality_by_dimension.png',dpi=200); plt.close(fig)

# ---------- Fig 3: cost vs quality scatter ----------
fig,axs=plt.subplots(2,3,figsize=(12,7.2))
panels=[('all_overall','Overall (mean of 4)')]+[(f'all_{d}',d) for d in dims]
for ax,(col,ttl) in zip(axs.flat,panels):
    for _,r in df.iterrows():
        full=r.dataset=='D01'
        ax.scatter(r.tokens/1e3,r[col],s=60,marker='o',facecolor=C[r['mode']] if full else SURF,edgecolor=C[r['mode']],lw=1.6,zorder=3)
        ax.annotate(r.run,(r.tokens/1e3,r[col]),xytext=(4,4),textcoords='offset points',fontsize=7.5,color=INK2)
    ax.set_title(ttl); ax.set_xlabel('Total tokens (thousands)'); ax.set_ylabel('Mean score (1–5)'); ax.grid(color=GRID,lw=0.6,zorder=0); ax.set_axisbelow(True)
ax=axs.flat[5]; ax.axis('off')
ax.legend(handles=[Line2D([],[],marker='o',ls='',color=C[S],label='Single agent'),Line2D([],[],marker='o',ls='',color=C[M],label='Multi-agent debate'),
   Line2D([],[],marker='o',ls='',mfc=SURF,mec=INK2,mew=1.6,label='Different corpus (D02–D04):\nnot directly comparable')],loc='center',frameon=False,fontsize=10)
rho=d1[['tokens','all_overall']].corr(method='spearman').iloc[0,1]
ax.text(0.5,0.18,f'Spearman ρ (tokens vs overall,\nD01 runs, n=11) = {rho:.2f}',ha='center',fontsize=10,color=INK,transform=ax.transAxes)
fig.suptitle('Cost vs quality: more tokens did not buy higher scores',x=0.01,ha='left',fontweight='bold',fontsize=12.5,color=INK)
fig.tight_layout(rect=(0,0,1,0.95)); fig.savefig(OUT+'fig3_cost_vs_quality.png',dpi=200); plt.close(fig)

# ---------- Fig 4: by rounds completed ----------
fig,axs=plt.subplots(2,3,figsize=(12,7.2))
panels=[('all_overall','Overall (mean of 4)')]+[(f'all_{d}',d) for d in dims]+[('tokens','Total tokens (thousands)')]
for ax,(col,ttl) in zip(axs.flat,panels):
    sc=1e3 if col=='tokens' else 1
    for k,rd in enumerate([1,2]):
        vals={m:d1[(d1['mode']==m)&(d1.rounds==rd)][col].values/sc for m in (S,M)}
        bars(ax,k,vals,fmt='{:.0f}' if col=='tokens' else '{:.2f}')
        for i,m in enumerate([S,M]):
            ax.text(k+(i-0.5)*0.36,0,f'n={len(vals[m])}',ha='center',va='top',fontsize=8,color=INK2,transform=ax.get_xaxis_transform()) if False else None
        nl=f"n={len(vals[S])} | n={len(vals[M])}"
        ax.text(k,-0.13,nl,ha='center',va='top',fontsize=8,color=INK2,transform=ax.get_xaxis_transform())
    ax.set_xticks([0,1]); ax.set_xticklabels(['1 round','2 rounds']); ax.set_title(ttl); style(ax)
    ax.set_xlabel('Critique/debate rounds completed',labelpad=16)
    if col!='tokens': ax.set_ylim(0,5.2)
    else: ax.margins(y=0.15)
fig.suptitle('Quality and cost by number of critique/debate rounds completed (D01 runs)',x=0.01,ha='left',fontweight='bold',fontsize=12.5,color=INK)
legend(fig,0.955); fig.tight_layout(rect=(0,0.03,1,0.92))
fig.text(0.01,0.005,'Rounds = highest round with a successful critique call (early stop when no changes proposed). n shown as single | multi; a single run has no SD. Scores are on final outputs only, so per-round trajectories are not measured.',fontsize=8,color=INK2)
fig.savefig(OUT+'fig4_by_rounds.png',dpi=200); plt.close(fig)
