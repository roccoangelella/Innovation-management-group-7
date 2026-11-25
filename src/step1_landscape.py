"""Step 1: exploratory source-only preview or verified TIP metadata analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ID = "docdb_family_id"
APP = "appln_id"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return pd.read_csv(path, dtype={ID:"string", APP:"string", "person_id":"string"})

def years(s):
    v = pd.to_numeric(s, errors="coerce")
    return v.where(v.between(1800, 2100) & (v % 1 == 0))

def rate(n, base):
    return n.div(base.where(base > 0)).sub(1).mul(100)

def volume(frame, cfg, benchmark=None):
    y = pd.Index(range(cfg["year_min"],cfg["year_max"]+1),name="year")
    n = frame.groupby("year").size().reindex(y,fill_value=0)
    out = n.to_frame("n")
    out["truncated"] = y > cfg["last_complete_year"]
    out["moving_average_3y"] = n.rolling(3).mean()
    out["yoy_pct"] = rate(n,n.shift())
    out["index_2000_or_start"] = n / n.iloc[0] * 100 if n.iloc[0] else np.nan
    if benchmark is not None:
        b = benchmark.set_index("year")["n"].reindex(y)
        out["global_n"] = b
        out["global_yoy_pct"] = rate(b,b.shift())
        out["global_index"] = b / b.iloc[0] * 100 if pd.notna(b.iloc[0]) and b.iloc[0]>0 else np.nan
        out["sector_share_pct"] = n.div(b.where(b>0))*100
    for col in out.columns.difference(["n","truncated","global_n"]):
        out.loc[out.truncated,col] = np.nan
    return out

def growth_table(v,cfg):
    rows=[]
    for start,end in [(cfg["year_min"],cfg["last_complete_year"]),cfg["recent_growth_window"]]:
        if start>=end or end>cfg["last_complete_year"] or start not in v.index or end not in v.index:
            continue
        for col in ["n","global_n"]:
            if col not in v: continue
            a,b=v.loc[start,col],v.loc[end,col]
            rows.append({"series":col,"start":start,"end":end,"start_n":a,"end_n":b,
                         "growth_pct":(b/a-1)*100 if a>0 and pd.notna(b) else np.nan,
                         "cagr_pct":((b/a)**(1/(end-start))-1)*100 if a>0 and pd.notna(b) else np.nan})
    return pd.DataFrame(rows)

def fractional(units, links, unit, category, entity=None, weight=None):
    """Conserve mass; include explicit Unknown rather than inflate observed categories."""
    pairs = links.dropna(subset=[unit]).copy()
    pairs[category] = pairs[category].fillna("Unknown").astype(str).str.strip().replace("","Unknown")
    if weight:
        pairs[weight]=pd.to_numeric(pairs[weight],errors="coerce")
        pairs=pairs[pairs[weight]>0].groupby([unit,category],as_index=False)[weight].sum()
    else:
        keys=[unit,category]+([entity] if entity else [])
        if entity:
            pairs=pairs.dropna(subset=[entity])
            if pairs.groupby([unit,entity])[category].nunique().gt(1).any():
                raise ValueError("Conflicting category for the same person and unit")
        pairs=pairs.drop_duplicates(keys)
        pairs["weight"]=1.0
        weight="weight"
    pairs=units[[unit,"year"]].merge(pairs[[unit,category,weight]],on=unit,how="left")
    pairs[category]=pairs[category].fillna("Unknown")
    pairs[weight]=pairs[weight].fillna(1.0)
    pairs["n_frac"]=pairs[weight]/pairs.groupby(unit)[weight].transform("sum")
    return pairs.groupby(["year",category],as_index=False)["n_frac"].sum()

def mix_outputs(table, category, cfg, out, name):
    table.to_csv(out/(name+"_annual.csv"),index=False)
    complete=table[table.year<=cfg["last_complete_year"]]
    total=complete.groupby(category)["n_frac"].sum().sort_values(ascending=False)
    (total.to_frame().assign(share_pct=total/total.sum()*100)).to_csv(out/(name+"_summary.csv"))
    periods=[]
    for lo,hi in cfg["comparison_periods"]:
        t=complete[complete.year.between(lo,hi)].groupby(category)["n_frac"].sum()
        if t.sum():
            periods.append(t.div(t.sum()).mul(100).rename(f"{lo}-{hi}"))
    if periods:
        pd.concat(periods,axis=1).fillna(0).to_csv(out/(name+"_period_shares.csv"))
    top=total.drop("Unknown",errors="ignore").head(cfg["top_n"]).index
    t=table.copy()
    t[category]=t[category].where(t[category].isin([*top,"Unknown"]),"Other")
    w=t.pivot_table(index="year",columns=category,values="n_frac",aggfunc="sum",fill_value=0)
    if w.empty: return
    share=w.div(w.sum(axis=1),axis=0)*100
    fig,ax=plt.subplots(figsize=(10,5))
    share.plot.area(ax=ax,linewidth=0,colormap="tab20")
    shade(ax,cfg)
    ax.set(ylabel="Fractional share (%)",ylim=(0,100),title=name.replace("_"," "))
    ax.legend(loc="center left",bbox_to_anchor=(1,0.5),fontsize=8)
    fig.savefig(out/(name+".png"),dpi=160,bbox_inches="tight")
    plt.close(fig)

def shade(ax,cfg):
    ax.axvspan(cfg["last_complete_year"]+0.5,cfg["year_max"]+0.5,color="grey",alpha=.17)
    ax.set_xlim(cfg["year_min"]-.5,cfg["year_max"]+.5)
    ax.set_xlabel("Year (grey = incomplete)")

def volume_outputs(units,cfg,out,name,benchmark=None):
    v=volume(units,cfg,benchmark)
    v.to_csv(out/(name+"_annual.csv"))
    growth_table(v,cfg).to_csv(out/(name+"_growth.csv"),index=False)
    fig,ax=plt.subplots(figsize=(9,4))
    ax.plot(v.index,v.n,label="Observed",marker=".",linewidth=1.6)
    ax.plot(v.index,v.moving_average_3y,label="3-year mean")
    shade(ax,cfg)
    ax.set(ylabel="Count",title=name.replace("_"," "))
    ax.legend()
    fig.savefig(out/(name+".png"),dpi=160,bbox_inches="tight")
    plt.close(fig)
    if "global_index" in v:
        fig,ax=plt.subplots(figsize=(9,4))
        v[["index_2000_or_start","global_index"]].rename(columns={"index_2000_or_start":"Sector","global_index":"Global"}).plot(ax=ax)
        shade(ax,cfg)
        ax.set(ylabel="Start year = 100",title=name+" relative growth")
        fig.savefig(out/(name+"_benchmark.png"),dpi=160,bbox_inches="tight")
        plt.close(fig)
    return v

def parse_cpc(s):
    return s.astype("string").str.replace(r"\s+","",regex=True).str.extract(r"^([A-HY]\d{2}[A-Z])",expand=False)

def in_window(frame,cfg):
    return frame[frame.year.between(cfg["year_min"],cfg["year_max"])].copy()

def metadata(input_path,folder,cfg,source):
    m=json.loads((folder/"manifest.json").read_text())
    if m["input_sha256"]!=digest(input_path) or m["config"]!=cfg:
        raise ValueError("Metadata does not match input/config")
    names=["applications","cpc","persons","wipo","wipo_names","global_families","global_applications"]
    data={}
    for name in names:
        path=folder/(name+".csv")
        if digest(path)!=m["sha256"][name]: raise ValueError("Metadata hash mismatch: "+name)
        data[name]=read(path)
        if len(data[name])!=m["counts"][name]: raise ValueError("Metadata count mismatch")
    a=data["applications"]
    if a[APP].isna().any() or a[APP].duplicated().any() or not set(a[ID]).issubset(set(source[ID])):
        raise ValueError("Invalid application identifiers")
    for name in ["cpc","persons","wipo"]:
        if not set(data[name][APP]).issubset(set(a[APP])): raise ValueError("Unmatched application link: "+name)
    for name in ["global_families","global_applications"]:
        b=data[name]
        if b.year.duplicated().any() or b.n.le(0).any(): raise ValueError("Invalid global denominator")
    return m,data

def analyze(input_path,out,cfg,folder=None,semantic="none",revision=None):
    out.mkdir(parents=True,exist_ok=True)
    source=read(input_path)
    if source[ID].isna().any() or source[ID].duplicated().any() or not source[ID].str.fullmatch(r"[1-9]\d*").all():
        raise ValueError("Expected unique positive family IDs")
    if "model_decision" not in source or not source.model_decision.eq(1).all(): raise ValueError("Expected retained positives")
    report={"input_sha256":digest(input_path),"input_families":len(source),"config":cfg,
            "status":"provisional model-selected corpus; not verified sector census","mode":"source_preview"}
    if folder:
        m,d=metadata(input_path,folder,cfg,source)
        report.update(mode="TIP_"+m["environment"],edition=m["edition"],metadata_sha256=m["sha256"])
        a=d["applications"].copy()
        a["priority"]=years(a.earliest_filing_year)
        a["year"]=years(a.appln_filing_year)
        f=a.groupby(ID,as_index=False).priority.min().rename(columns={"priority":"year"})
        report["no_PI_application"]=len(source)-len(f)
        report["missing_priority_year"]=int(f.year.isna().sum())
        report["missing_application_year"]=int(a.year.isna().sum())
        units_f=in_window(f,cfg); units_a=in_window(a,cfg)
        report["family_outside_window"]=int(f.year.notna().sum()-len(units_f))
        report["family_in_window"]=len(units_f)
        source=source.drop(columns=["year"],errors="ignore").merge(f,on=ID,how="inner")
        c=d["cpc"].assign(subclass=parse_cpc(d["cpc"].cpc_class_symbol))
        w=d["wipo"].merge(d["wipo_names"].drop_duplicates("techn_field_nr"),on="techn_field_nr",how="left",validate="many_to_one")
        persons=d["persons"]
        for level,units,key,global_name in [("family",units_f,ID,"global_families"),("application",units_a,APP,"global_applications")]:
            v=volume_outputs(units,cfg,out,level,d[global_name])
            if (v.n>v.global_n).any(): raise ValueError("Sector exceeds global denominator")
            def attach(t):
                return t.merge(a[[APP,ID]],on=APP,validate="many_to_one") if key==ID else t
            mix_outputs(fractional(units,attach(c.dropna(subset=["subclass"])),key,"subclass"),"subclass",cfg,out,level+"_cpc")
            for cat in ["techn_field","techn_sector"]:
                mix_outputs(fractional(units,attach(w),key,cat,weight="weight"),cat,cfg,out,level+"_wipo_"+cat)
            for role,col in [("applicant","applt_seq_nr"),("inventor","invt_seq_nr")]:
                links=attach(persons[persons[col].fillna(0)>0])
                mix_outputs(fractional(units,links,key,"country",entity="person_id"),"country",cfg,out,level+"_"+role)
        off=a[[ID,APP,"appln_auth","appln_kind"]].copy()
        off["office"]=off.appln_auth.fillna("Unknown").str.strip().replace("","Unknown")
        off["pct"]=(off.office=="WO") & off.appln_kind.fillna("").str.startswith("W")
        for level,units,key in [("family",units_f,ID),("application",units_a,APP)]:
            o=units[[key,"year"]].merge(off[[key,"office","pct"]],on=key)
            t=o.drop_duplicates([key,"office"]).groupby(["year","office"]).size().rename("n").reset_index()
            t["pct_of_units"]=t.n/t.year.map(units.groupby("year").size())*100
            t.to_csv(out/(level+"_offices.csv"),index=False)
            pct=o[o.pct].drop_duplicates(key).groupby("year").size().reindex(range(cfg["year_min"],cfg["year_max"]+1),fill_value=0)
            pct.rename("pct_units").to_csv(out/(level+"_pct.csv"),index_label="year")
        breadth=off[~off.office.isin(["WO","Unknown"])].groupby(ID).office.nunique()
        profile=units_f.assign(distinct_non_WO_offices=units_f[ID].map(breadth))
        profile.groupby("year").distinct_non_WO_offices.agg(["count","mean"]).to_csv(out/"family_office_breadth.csv")
        # Families may appear at several offices; never normalize overlapping office counts to 100%.
        t=pd.read_csv(out/"family_offices.csv")
        fig,ax=plt.subplots(figsize=(9,4))
        for office in ["CN","EP","US","JP","KR"]:
            g=t[t.office==office]
            ax.plot(g.year,g.n,label=office)
        shade(ax,cfg); ax.set(ylabel="Families with a filing",title="IP5 filing offices")
        ax.legend(); fig.savefig(out/"family_offices.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    else:
        source["year"]=years(source["year"] if "year" in source else source["earliest_filing_year"])
        report["missing_priority_proxy"]=int(source.year.isna().sum())
        report["family_in_window"]=len(in_window(source,cfg))
        volume_outputs(in_window(source,cfg),cfg,out,"family_priority_proxy")
        if "source_query" in source:
            in_window(source,cfg).groupby(["year","source_query"]).size().rename("n").to_csv(out/"query_origin_annual.csv")
        report["blocked"]=["global benchmark","complete CPC mix","WIPO fields","applicant/inventor countries","office/PCT indicators"]
    if semantic!="none":
        from step1_semantic import cluster
        report["semantic"]=cluster(source,out,cfg,semantic,revision)
    (out/"manifest.json").write_text(json.dumps(report,indent=2))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("data/final/humanoid_patents_final.csv"))
    p.add_argument("--out",type=Path,default=Path("outputs/step1_preview"))
    p.add_argument("--config",type=Path,default=Path("config/step1.json"))
    p.add_argument("--metadata",type=Path)
    p.add_argument("--semantic",choices=["none","tfidf","patent"],default="tfidf")
    p.add_argument("--revision",help="Hugging Face model commit (required for patent mode)")
    a=p.parse_args()
    if a.out.exists() and any(a.out.iterdir()):
        raise ValueError("Choose an empty output directory to avoid mixing run results")
    print(json.dumps(analyze(a.input,a.out,json.loads(a.config.read_text()),a.metadata,a.semantic,a.revision),indent=2))
if __name__=="__main__":
    main()
