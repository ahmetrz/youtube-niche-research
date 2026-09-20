import os, zipfile, subprocess, json
from pathlib import Path
import pandas as pd
import numpy as np

DATA=Path("tmpdata"); OUT=Path("data")
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

def dl(ds, fn):
    p=DATA/fn
    if p.exists(): return p
    subprocess.run(["python","-m","kaggle","datasets","download",ds,"-f",fn,"-p",str(DATA)],check=True)
    z=DATA/(fn+".zip")
    if z.exists():
        with zipfile.ZipFile(z) as a: a.extractall(DATA)
    return p

us=pd.read_csv(dl("bsthere/youtube-trending-videos-stats-2026","US_Trending.csv"))
gb=pd.read_csv(dl("bsthere/youtube-trending-videos-stats-2026","GB_Trending.csv"))
ch=pd.read_csv(dl("xtitanixx/youtube-2025-channels","youtube_channel_info_v2.csv"))
v=pd.concat([us.assign(market="US"),gb.assign(market="GB")],ignore_index=True)
agg=v.groupby("video_id").agg(days_trending=("trending_date","nunique"),markets=("market","nunique")).reset_index()
v=v.sort_values("views").drop_duplicates("video_id",keep="last").merge(agg,on="video_id")
cc=["channel_id","subscriber_count","views_last_30_days","videos_last_30_days"]
m=v.merge(ch[cc],on="channel_id",how="inner")
m=m[(m.subscriber_count.between(1000,2000000)) & (m.views_last_30_days>0) & (m.videos_last_30_days>0)].copy()
# Remove categories dominated by music/gaming/film and obvious official/promotional/news noise.
m=m[~m.category_id.isin([1,10,20])]
bad=r"#shorts|official trailer|main trailer|teaser|official video|official audio|episode [0-9]|breaking news|live:"
m=m[~m.title.str.contains(bad,case=False,na=False,regex=True)]
chanbad=r"warner|netflix|disney|sony|universal|forbes|times now|news|tv|records|music"
m=m[~m.channel_title.str.contains(chanbad,case=False,na=False,regex=True)]
m["baseline"]=m.views_last_30_days/m.videos_last_30_days
m["relative"]=m.views/m.baseline
m["views_per_sub"]=m.views/m.subscriber_count
m=m[(m.views>=100000)&(m.relative>=1.5)]
m["outlier_score"]=np.log1p(m.relative)*np.log1p(m.views_per_sub+1)*np.log1p(m.days_trending+1)
cols=["title","channel_title","views","subscriber_count","baseline","relative","views_per_sub","days_trending","markets","category_id","video_id","outlier_score"]
m=m.sort_values(["outlier_score","views"],ascending=False)[cols].head(1000)
records=json.loads(m.replace({np.nan:None}).to_json(orient="records"))
(OUT/"outliers.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
print("Wrote",len(records),"clean outliers")
