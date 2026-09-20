# YouTube Opportunity Research — False-Positive-Resistant Architecture

## Objective
Discover repeatable, faceless, long-form YouTube micro-niches where independent small/medium channels repeatedly outperform their own normal baseline. A viral video is evidence, never a niche by itself.

## Core principle
The system has two separate stages:
1. **Candidate recall** — collect broadly.
2. **Evidence precision** — reject false positives aggressively before a niche can be promoted.

No candidate reaches the final shortlist from title heuristics alone.

## Pipeline

### 1. Ingestion
Use multiple datasets rather than one trending feed.
Canonical video schema:
video_id, channel_id, title, published_at, market, views, likes, comments, duration_seconds, category_id, subscriber_count, channel_views, channel_video_count, recent_channel_views, recent_upload_count.

Store source provenance and collection timestamp for every observation.

### 2. Deduplication / temporal normalization
A video appearing on multiple trending days is one video.
Preserve:
- maximum/latest observed views
- number of trending days
- number of markets
- first/last observation
Never treat daily repetitions as independent evidence.

### 3. Hard exclusion layer
Reject before scoring:
- Shorts / likely Shorts
- music and music videos
- film/TV trailers and official promotional material
- full episodes / clips whose value depends on copyrighted broadcast footage
- livestreams
- breaking/current-news clips
- political/current-affairs clips
- official sports highlights / broadcast clips
- corporate product launch/promotional videos
- major broadcasters, studios, labels, leagues and institutional media
- celebrity-driven virality where the transferable topic is absent
- channels outside configured size bounds
- zero/invalid channel baselines
- duplicate/reuploads

Duration metadata is authoritative for Shorts when available; title patterns are only fallback evidence.

### 4. Channel-type classifier
Classify each channel:
INDEPENDENT_CREATOR, CREATOR_BUSINESS, CORPORATE_BRAND, BROADCASTER_NEWS, SPORTS_RIGHTSHOLDER, LABEL_STUDIO, INSTITUTION, UNKNOWN.
Only the first two are normally eligible. UNKNOWN is quarantined for validation, not automatically accepted.

Signals:
channel name, description/category when available, upload frequency, subscriber scale, title vocabulary, known-entity denylist, repeated content patterns.

### 5. Video-type classifier
Classify:
EVERGREEN_EXPLAINER, DOCUMENTARY_STORY, EXPERIMENT_TEST, RESTORATION_TRANSFORMATION, DATA_ANALYSIS, ORIGINAL_SPORTS_ANALYSIS, PERSONALITY_VLOG, NEWS_EVENT, PROMO_TRAILER, BROADCAST_CLIP, SHORT_FORM, OTHER.
Eligible types are configurable. News/promo/broadcast/short-form are excluded from evergreen niche discovery.

### 6. Robust outlier model
Never divide by a zero baseline.
Use several signals rather than a single ratio:
- log views
- views/subscribers
- performance vs recent channel median/expected views
- age-normalized velocity when publish date exists
- engagement residual when likes/comments exist
- multi-day persistence
- multi-market spread
- channel-size penalty
Winsorize extreme ratios. Require minimum evidence quality.

### 7. Transferability test
A high-performing video must answer:
Could a new faceless channel reproduce the value without access to this creator, celebrity, event, IP, broadcast footage, expensive physical setup or proprietary access?
Reject when answer is no.

### 8. Topic extraction and clustering
Normalize titles, remove entity/event noise, extract subject + format + viewer promise.
Cluster semantically similar candidates.
Examples of useful cluster dimensions:
- mechanism/explanation
- hidden failure/cause
- reconstruction
- restoration
- engineering test
- tactical/sports reconstruction
- overlooked historical system
Do not define a niche from one keyword.

### 9. Repetition requirement
A micro-niche candidate needs independent evidence:
- >=3 qualifying videos
- >=2 independent eligible channels
- preferably spread over multiple dates
- no single channel contributes >50% of evidence
Single-video clusters stay in WATCHLIST.

### 10. False-positive audit
Every promoted cluster gets explicit rejection tests:
- Is performance caused by a celebrity/name?
- breaking event?
- copyrighted footage?
- official access?
- Shorts distribution?
- established brand audience?
- one-off curiosity?
- giveaway/challenge prize?
- controversy?
- geographic anomaly?
- stale subscriber metadata?
- baseline denominator artifact?
- duplicate syndication?
If material uncertainty remains, mark NEEDS_VALIDATION.

### 11. Opportunity validation
Only after dataset evidence:
- current YouTube search competition
- recent upload supply
- Google Trends/demand direction where useful
- real channel/video examples
- 100-video topic depth
- faceless production feasibility
- Seedance/AI visual feasibility
- copyright/monetization risk

### 12. Outputs
Generate:
- data/candidates.json — broad candidates
- data/rejected.json — excluded rows + reasons
- data/outliers.json — precision-filtered eligible outliers
- data/clusters.json — repeated micro-niche evidence
- data/watchlist.json — promising but insufficient evidence
- reports/quality.json — counts, rejection reasons, unknown rates, data coverage

## Promotion gates
FINAL_CANDIDATE only if:
- eligible channel type
- eligible video type
- not Short
- valid robust baseline
- transferable
- repeated across independent channels
- sustainable topic depth
- acceptable copyright/monetization risk
- current validation supports demand

The system should prefer returning zero final niches over returning a false opportunity.
