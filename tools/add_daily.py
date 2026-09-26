#!/usr/bin/env python3
"""Append (or replace, if today's slug exists) one 每日简报 daily briefing.

Usage:
    python3 tools/add_daily.py /tmp/daily.json --note "一句话说明"

/tmp/daily.json format:
    {"title": "...", "dek": "...", "tags": [...],
     "sources": [{"url":..., "date":..., "site":..., "title":...}, ...],
     "region": "国内外", "layers": ["compute", ...],
     "body_md": "...markdown..."}

Updates: articles_daily.json, article_details/daily-YYYY-MM-DD.json,
facets.json (latest.dailies), overview.json (counts, latestDailies, runs),
then regenerates api-data.js. Prints a JSON report.
"""
import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser('~')
BACKUP = os.path.join(HOME, 'workspace/publish/ai4s_api_backup')
TOOLS = os.path.join(HOME, 'workspace/publish/ai4s/tools')
REQUIRED = ['title', 'dek', 'tags', 'sources', 'region', 'layers', 'body_md']

CST = timezone(timedelta(hours=8))
now_utc = datetime.now(timezone.utc)
today_cst = datetime.now(CST).date().isoformat()


def fail(msg):
    print(json.dumps({'error': msg}, ensure_ascii=False))
    sys.exit(2)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--note', default='')
    a = ap.parse_args()
    try:
        d = json.load(open(a.input))
    except Exception as e:
        fail('cannot read input: %s' % e)

    missing = [k for k in REQUIRED if not d.get(k)]
    if missing:
        fail('missing fields: %s' % ','.join(missing))
    if not isinstance(d['sources'], list) or not d['sources']:
        fail('sources must be a non-empty list')
    for s in d['sources']:
        if not all(s.get(k) for k in ('url', 'site', 'title')):
            fail('each source needs url/site/title')
    bl = len(d['body_md'])
    if bl < 800 or bl > 8000:
        fail('body_md length %d out of 800..8000' % bl)

    slug = 'daily-' + today_cst
    daily_path = os.path.join(BACKUP, 'articles_daily.json')
    dailies = json.load(open(daily_path))['items']

    existing = next((x for x in dailies if x['slug'] == slug), None)
    if existing:
        art_id, issue_no = existing['id'], existing['issue_no']
        dailies = [x for x in dailies if x['slug'] != slug]
        replaced = True
    else:
        mx = 0
        for k in ('report', 'daily', 'weekly'):
            p = os.path.join(BACKUP, f'articles_{k}.json')
            if os.path.exists(p):
                for x in json.load(open(p))['items']:
                    mx = max(mx, x.get('id', 0))
        art_id = mx + 1
        issue_no = max([x.get('issue_no', 0) for x in dailies] + [0]) + 1
        replaced = False

    entry = {
        'id': art_id, 'slug': slug, 'title': d['title'], 'kind': 'daily',
        'dek': d['dek'], 'tags': d['tags'], 'sources': d['sources'],
        'region': d.get('region', '国内外'), 'layers': d['layers'],
        'issue_no': issue_no, 'pinned': False, 'word_count': len(d['body_md']),
        'published_at': now_utc.isoformat(), 'body_md': d['body_md'],
    }
    dailies.insert(0, entry)
    json.dump({'items': dailies}, open(daily_path, 'w'), ensure_ascii=False, indent=2)

    det_path = os.path.join(BACKUP, 'article_details', slug + '.json')
    json.dump(entry, open(det_path, 'w'), ensure_ascii=False, indent=2)

    fac_path = os.path.join(BACKUP, 'facets.json')
    facets = json.load(open(fac_path))
    facets['latest']['dailies'] = now_utc.isoformat()
    json.dump(facets, open(fac_path, 'w'), ensure_ascii=False, indent=2)

    ov_path = os.path.join(BACKUP, 'overview.json')
    ov = json.load(open(ov_path))
    if not replaced:
        ov['counts']['dailies'] += 1
        ov['counts']['articles'] += 1
    ov['latestDailies'] = [dict(x) for x in dailies[:12]]
    ov.setdefault('runs', []).insert(0, {
        'run_date': today_cst, 'job': 'daily', 'status': 'ok', 'added': 1,
        'note': a.note or ('发布第 %d 期每日简报' % issue_no),
        'created_at': now_utc.isoformat(),
    })
    json.dump(ov, open(ov_path, 'w'), ensure_ascii=False, indent=2)

    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'regen_api_data.py')],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail('regen failed: %s' % (r.stderr or r.stdout))

    print(json.dumps({
        'created': True, 'replaced': replaced, 'issue_no': issue_no,
        'slug': slug, 'title': d['title'], 'id': art_id,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
