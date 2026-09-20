import json, re
from collections import defaultdict, Counter
from pathlib import Path

IN=Path("data/outliers.json"); OUT=Path("data")
rows=json.loads(IN.read_text(encoding="utf-8"))

STOP=set("""the a an and or of to in on for with vs is are was were why how what this that from after before new gets get got i you we they it at by as into under over more just can can't your my our their""".split())
FORMAT_RULES={
 "restoration_transformation":r"restor|cleaned|repair|rebuild|reviv|detail",
 "experiment_test":r"test|challenge|what happens|pushing|trying|bought",
 "mechanism_explainer":r"why |how |can't|truth|explained|science|works",
 "engineering_technology":r"battery|engine|car|power|technology|solid state|tuning",
 "sports_original_analysis":r"penalty|tactic|football|shooting challenge|premier league",
}

def tokens(s):
 s=re.sub(r"[^a-z0-9 ]"," ",s.lower())
 return [x for x in s.split() if len(x)>2 and x not in STOP and not x.isdigit()]

def fmt(title):
 for k,p in FORMAT_RULES.items():
  if re.search(p,title,re.I): return k
 return "other"

for r in rows:
 r["format_cluster"]=fmt(r["title"])
 r["_tokens"]=tokens(r["title"])

groups=defaultdict(list)
for r in rows:
 groups[r["format_cluster"]].append(r)

clusters=[]
watch=[]
for name,items in groups.items():
 chans=set(x["channel_title"] for x in items)
 # Cross-channel repeated vocabulary is a lightweight deterministic semantic proxy.
 freq=Counter(t for x in items for t in set(x["_tokens"]))
 shared=[t for t,n in freq.most_common(12) if n>=2]
 evidence=[{k:x[k] for k in ["title","channel_title","views","subscriber_count","relative","video_id"]} for x in items]
 obj={"cluster":name,"video_count":len(items),"independent_channels":len(chans),"shared_terms":shared,"evidence":evidence}
 if name!="other" and len(items)>=3 and len(chans)>=2:
  obj["status"]="CANDIDATE_FOR_EXTERNAL_VALIDATION"; clusters.append(obj)
 else:
  obj["status"]="WATCHLIST"; watch.append(obj)

(OUT/"clusters.json").write_text(json.dumps(clusters,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"watchlist.json").write_text(json.dumps(watch,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"clusters":len(clusters),"watchlist_groups":len(watch)},indent=2))
