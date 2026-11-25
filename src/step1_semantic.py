"""Exploratory fixed-seed clustering: CPU lexical baseline or course patent SBERT."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.preprocessing import normalize

def cluster(source,out,cfg,method,revision):
    f=source.dropna(subset=["abstract_en"]).copy()
    f=f[f.abstract_en.str.strip().ne("")].sort_values("docdb_family_id").reset_index(drop=True)
    text=f.abstract_en.tolist()
    if len(f)<=cfg["clusters"]: raise ValueError("Not enough abstracts for clustering")
    stop=sorted(ENGLISH_STOP_WORDS|set("said wherein whereby thereof comprising comprises comprise plurality configured invention embodiment embodiments device devices apparatus system systems method methods first second robot robots humanoid robotic".split()))
    tf=TfidfVectorizer(stop_words=stop,ngram_range=(1,2),min_df=2,max_df=.8,sublinear_tf=True,max_features=25000)
    lexical=tf.fit_transform(text)
    if method=="patent":
        if not revision or not __import__("re").fullmatch("[0-9a-f]{40}",revision):
            raise ValueError("Pin a 40-character model commit with --revision")
        from sentence_transformers import SentenceTransformer
        model=SentenceTransformer(cfg["patent_model"],revision=revision)
        x=normalize(model.encode(text,batch_size=64,show_progress_bar=True,normalize_embeddings=True))
        truncated=sum(len(model.tokenizer(t,truncation=False)["input_ids"])>model.max_seq_length for t in text)
    else:
        x=lexical
        truncated=None
    k=cfg["clusters"]
    km=KMeans(n_clusters=k,n_init=10,random_state=cfg["seed"]).fit(x)
    labels=km.labels_
    f["cluster"]=labels
    f[["docdb_family_id","year","cluster"]].to_csv(out/"semantic_assignments.csv",index=False)
    terms=tf.get_feature_names_out()
    rows=[]
    distances=km.transform(x)
    for i in range(k):
        idx=np.flatnonzero(labels==i)
        if not len(idx): continue
        weights=np.asarray(lexical[idx].mean(axis=0)).ravel()
        top=terms[np.argsort(weights)[-12:][::-1]]
        reps=idx[np.argsort(distances[idx,i])[:5]]
        rows.append({"cluster":i,"n":len(idx),"top_terms":"; ".join(top),
                     "representative_family_ids":"; ".join(f.iloc[reps].docdb_family_id)})
    pd.DataFrame(rows).to_csv(out/"semantic_clusters.csv",index=False)
    trend=f[f.year.between(cfg["year_min"],cfg["year_max"])].groupby(["year","cluster"]).size().rename("n").reset_index()
    trend["share_pct"]=trend.n/trend.groupby("year").n.transform("sum")*100
    trend.to_csv(out/"semantic_annual.csv",index=False)
    sample=min(1000,len(f))
    silhouette=float(silhouette_score(x,labels,sample_size=sample,random_state=cfg["seed"],metric="cosine")) if len(set(labels))>1 else None
    repeat=KMeans(n_clusters=k,n_init=10,random_state=cfg["seed"]+1).fit_predict(x)
    return {"method":method,"model":cfg["patent_model"] if method=="patent" else None,
            "revision":revision if method=="patent" else None,"n":len(f),"k":k,
            "cosine_silhouette_sample":silhouette,"seed_stability_ARI":float(adjusted_rand_score(labels,repeat)),
            "truncated_abstracts":truncated,"status":"exploratory clusters, not validated technology labels"}
