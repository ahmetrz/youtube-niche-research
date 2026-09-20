import os, zipfile, subprocess
from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException

app = FastAPI(title="YouTube Niche Research API")
DATA=Path("/tmp/ytdata")
DATA.mkdir(exist_ok=True)

def kaggle_download(dataset, filename):
    path=DATA/filename
    if path.exists(): return path
    env=os.environ.copy()
    token=env.get("KAGGLE_API_TOKEN")
    if not token: raise HTTPException(500,"KAGGLE_API_TOKEN is not configured")
    subprocess.run(["python","-m","kaggle","datasets","download",dataset,"-f",filename,"-p",str(DATA)],check=True,env=env)
    z=DATA/(filename+".zip")
    if z.exists():
        with zipfile.ZipFile(z) as f: f.extractall(DATA)
    return path

@app.get("/")
def root():
    return {"status":"ok","service":"youtube-niche-research"}

@app.get("/outliers")
def outliers(limit:int=50):
    ds="bsthere/youtube-trending-videos-stats-2026"
    us=pd.read_csv(kaggle_download(ds,"US_Trending.csv"))
    gb=pd.read_csv(kaggle_download(ds,"GB_Trending.csv"))
    ch=pd.read_csv(kaggle_download("xtitanixx/youtube-2025-channels","youtube_channel_info_v2.csv"))
    v=pd.concat([us,gb],ignore_index=True).sort_values("views").drop_duplicates("video_id",keep="last")
    cols=["channel_id","subscriber_count","views_last_30_days","videos_last_30_days"]
    m=v.merge(ch[cols],on="channel_id",how="inner")
    m=m[~m.category_id.isin([1,10,20]) & (m.subscriber_count>=1000)]
    bad=r"#shorts|official trailer|teaser trailer|official video|official audio"
    m=m[~m.title.str.contains(bad,case=False,na=False)]
    valid=(m.videos_last_30_days>0)&(m.views_last_30_days>0)
    m=m[valid].copy()
    m["baseline"]=m.views_last_30_days/m.videos_last_30_days
    m["relative"]=m.views/m.baseline
    m=m[(m.views>=100000)&(m.relative>=1.5)]
    cols=["title","channel_title","views","subscriber_count","baseline","relative","category_id","video_id"]
    return m.sort_values(["relative","views"],ascending=False)[cols].head(min(limit,200)).replace({np.nan:None}).to_dict("records")
