#!/usr/bin/env python3
"""
爬均一教育平台,把每個單元(chapter)的「老師整理觀念大綱」抓下來。
大綱 = chapter 下各 section 標題 + section 內的 concept/example 影片標題。
輸出: junyi_outlines.json  { "正規化單元名": { "junyiTitle":..., "sections":[{title, points:[...]}], "url":... } }
"""
import re, json, time, urllib.request, sys
from pathlib import Path

OUT = Path(__file__).parent.parent / "junyi_outlines.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://www.junyiacademy.org/topics/"

# 各科要爬的均一 root topic id。math 用翰林版(h-),其他用通用結構。
ROOTS = {
    "數學": ["h-m7a", "h-m7b", "h-m8a", "h-m8b", "h-m9a", "h-m9b"],
    "生物": ["junyi-middle-school-biology"],
    "理化": ["middle-school-physics-chemistry"],
    "地科": ["junyi-middle-earth-science"],
    "英文": ["eng-junior07", "eng-junior08", "eng-junior09"],
    "國文": ["coocjun-c1", "coocjun-c2", "coocjun-c3"],
}

_cache = {}
def fetch_topic(tid):
    if tid in _cache: return _cache[tid]
    url = BASE + tid
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"    ✗ fetch {tid}: {e}", file=sys.stderr)
        _cache[tid] = None
        return None
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL)
    if not m:
        _cache[tid] = None
        return None
    try:
        data = json.loads(m.group(1))
        qs = data["props"]["pageProps"]["dehydratedState"]["queries"]
        d = qs[0]["state"]["data"]
    except Exception:
        _cache[tid] = None
        return None
    _cache[tid] = d
    time.sleep(0.15)
    return d

# 影片標題裡哪些算「觀念重點」
CONCEPT_RE = re.compile(r"【(觀念|概念|定義|公式|重點|整理|原理|定律|現象|結構|分類)】")

def clean_video_title(t):
    # 去掉前面的【觀念】【概念1】等標記留核心
    t = re.sub(r"^【[^】]*】\s*", "", t).strip()
    t = re.sub(r"^\d+[-.]\d+\s*", "", t)
    return t.strip()

def collect_concept_points(tid, depth=0, acc=None):
    """遞迴往下找 concept/觀念 類影片標題(深度限制避免爆量)"""
    if acc is None: acc = []
    if depth > 2 or len(acc) >= 12:
        return acc
    d = fetch_topic(tid)
    if not d: return acc
    for c in d.get("children", []):
        ctype = c.get("type")
        title = c.get("title", "")
        if ctype == "video":
            if CONCEPT_RE.search(title):
                p = clean_video_title(title)
                if p and p not in acc:
                    acc.append(p)
        elif ctype in ("child-topic", "topic") and c.get("hasChildren") is not False:
            ctid = c.get("topicId") or c.get("id")
            if ctid:
                collect_concept_points(ctid, depth + 1, acc)
        if len(acc) >= 12: break
    return acc

def walk_chapter(chapter):
    """chapter → sections:[{title, points}]。section 標題一定收,觀念點盡量收。"""
    sections = []
    children = chapter.get("children", [])
    if not children:
        return sections
    for sec in children:
        sec_tid = sec.get("topicId") or sec.get("id")
        sec_title = re.sub(r"\s+", " ", sec.get("title", "")).strip()
        if not sec_title: continue
        points = collect_concept_points(sec_tid) if sec_tid else []
        sections.append({"title": sec_title, "points": points})
    return sections

def norm_unit(name):
    """正規化單元名做 matching key:去前綴、編號、空白、括號註解"""
    n = name
    n = re.sub(r"【[^】]*】", "", n)
    n = re.sub(r"第[一二三四五六七八九十0-9]+[章課節單元]", "", n)
    n = re.sub(r"\d+[-.]\d+", "", n)
    n = re.sub(r"[(（][^)）]*[)）]", "", n)
    n = re.sub(r"\s+", "", n)
    return n.strip()

def main():
    outlines = {}
    for subj, roots in ROOTS.items():
        print(f"=== {subj} ===")
        for root in roots:
            d = fetch_topic(root)
            if not d:
                print(f"  ✗ {root} 抓不到")
                continue
            for chapter in d.get("children", []):
                ch_title = re.sub(r"\s+", " ", chapter.get("title", "")).strip()
                sections = walk_chapter(chapter)
                pt_count = sum(len(s["points"]) for s in sections)
                key = norm_unit(ch_title)
                if not key: continue
                ch_url = "https://www.junyiacademy.org/topics/" + (chapter.get("topicId") or chapter.get("id", ""))
                outlines[subj + "|" + key] = {
                    "subj": subj,
                    "junyiTitle": ch_title,
                    "sections": sections,
                    "url": ch_url,
                }
                print(f"  ✓ {ch_title}: {len(sections)} 節 / {pt_count} 重點")
    OUT.write_text(json.dumps(outlines, ensure_ascii=False, indent=1))
    print(f"\n共 {len(outlines)} 個單元大綱 → {OUT}")

if __name__ == "__main__":
    main()
