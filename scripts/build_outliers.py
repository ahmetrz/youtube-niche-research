import json, re, zipfile, subprocess
from pathlib import Path
import numpy as np
import pandas as pd

DATA=Path("tmpdata"); OUT=Path("data")
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
CFG=json.loads(Path("config/filters.json").read_text())

def dl(ds,fn):
    p=DATA/fn
    if p.exists(): return p
    subprocess.run(["python","-m","kaggle","datasets","download",ds,"-f",fn,"-p",str(DATA)],check=True)
    z=DATA/(fn+".zip")
    if z.exists():
        with zipfile.ZipFile(z) as a: a.extractall(DATA)
    return p

def reason(row):
    title=str(row.title); channel=str(row.channel_title)
    if row.category_id in CFG["excluded_categories"]: return "excluded_category"
    if CFG["exclude_news_category"] and row.category_id==CFG["news_category"]: return "news_current_affairs"
    if not (CFG["min_subscribers"] <= row.subscriber_count <= CFG["max_subscribers"]): return "channel_size"
    if row.views_last_30_days<=0 or row.videos_last_30_days<=0: return "invalid_baseline"
    if any(re.search(p,title,re.I) for p in CFG["title_deny_patterns"]): return "excluded_video_pattern"
    if any(re.search(p,channel,re.I) for p in CFG["channel_deny_patterns"]): return "institutional_media_or_brand"
    return None

us=pd.read_csv(dl("bsthere/youtube-trending-videos-stats-2026","US_Trending.csv")).assign(market="US")
gb=pd.read_csv(dl("bsthere/youtube-trending-videos-stats-2026","GB_Trending.csv")).assign(market="GB")
ch=pd.read_csv(dl("xtitanixx/youtube-2025-channels","youtube_channel_info_v2.csv"))
raw=pd.concat([us,gb],ignore_index=True)
agg=raw.groupby("video_id").agg(days_trending=("trending_date","nunique"),markets=("market","nunique")).reset_index()
v=raw.sort_values("views").drop_duplicates("video_id",keep="last").merge(agg,on="video_id")
cc=["channel_id","subscriber_count","views_last_30_days","videos_last_30_days"]
m=v.merge(ch[cc],on="channel_id",how="inner")
m["reject_reason"]=m.apply(reason,axis=1)
rej=m[m.reject_reason.notna()].copy()
m=m[m.reject_reason.isna()].copy()
m["baseline"]=m.views_last_30_days/m.videos_last_30_days
m["relative"]=m.views/m.baseline
m["relative_capped"]=m.relative.clip(upper=50)
m["views_per_sub"]=m.views/m.subscriber_count
m=m[(m.views>=CFG["min_views"])&(m.relative>=CFG["min_relative"])].copy()
m["outlier_score"]=np.log1p(m.relative_capped)*np.log1p(m.views_per_sub+1)*np.log1p(m.days_trending+1)
cols=["title","channel_title","views","subscriber_count","baseline","relative","views_per_sub","days_trending","markets","category_id","video_id","outlier_score"]
m=m.sort_values(["outlier_score","views"],ascending=False)[cols]
def dump(df,path,limit=None):
    if limit: df=df.head(limit)
    Path(path).write_text(df.replace({np.nan:None}).to_json(orient="records",indent=2,force_ascii=False),encoding="utf-8")
dump(m,OUT/"outliers.json",2000)
dump(rej[["title","channel_title","views","subscriber_count","category_id","video_id","reject_reason"]],OUT/"rejected.json",5000)
quality={"raw_rows":len(raw),"unique_videos":len(v),"channel_joined":len(m)+len(rej),"eligible_outliers":len(m),"rejected":len(rej),"rejection_reasons":rej.reject_reason.value_counts().to_dict()}
(OUT/"quality.json").write_text(json.dumps(quality,indent=2),encoding="utf-8")
print(json.dumps(quality,indent=2))
