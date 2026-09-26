#!/usr/bin/env python3
"""Append (or replace, if the slug exists) one 深度调研 deep-research report.

Usage:
    python3 tools/add_report.py /tmp/report.json --note "一句话说明"

/tmp/report.json format:
    {"slug": "report-<topic>", "title": "...", "dek": "...", "tags": [...],
     "sources": [{"url":..., "date":..., "site":..., "title":...}, ...],
     "region": "中国大陆", "layers": ["工具链与智能体", ...],
     "body_md": "...markdown..."}

Updates: articles_report.json, article_details/<slug>.json,
facets.json (latest.reports), overview.json (counts, latestReports, runs),
then regenerates api-data.js. Prints a JSON report.
"""
import json, os, re, sys, subprocess
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser('~')
BACKUP = os.path.join(HOME, 'workspace/publish/ai4s_api_backup')
TOOLS = os.path.join(HOME, 'workspace/publish/ai4s/tools')
REQUIRED = ['slug', 'title', 'dek', 'tags', 'sources', 'region', 'layers', 'body_md']

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
    if not d['slug'].startswith('report-'):
        fail('slug must start with report-')
    if not isinstance(d['sources'], list) or not d['sources']:
        fail('sources must be a non-empty list')
    for s in d['sources']:
        if not all(s.get(k) for k in ('url', 'site', 'title')):
            fail('each source needs url/site/title')
    cjk = len(re.findall(r'[\u4e00-\u9fff]', d['body_md']))
    if cjk < 3500 or cjk > 4500:
        fail('body_md CJK chars %d out of 3500..4500' % cjk)

    slug = d['slug']
    report_path = os.path.join(BACKUP, 'articles_report.json')
    reports = json.load(open(report_path))['items']

    existing = next((x for x in reports if x['slug'] == slug), None)
    if existing:
        art_id = existing['id']
        reports = [x for x in reports if x['slug'] != slug]
        replaced = True
    else:
        mx = 0
        for k in ('report', 'daily', 'weekly'):
            p = os.path.join(BACKUP, f'articles_{k}.json')
            if os.path.exists(p):
                for x in json.load(open(p))['items']:
                    mx = max(mx, x.get('id', 0))
        art_id = mx + 1
        replaced = False

    entry = {
        'id': art_id, 'slug': slug, 'title': d['title'], 'kind': 'report',
        'dek': d['dek'], 'tags': d['tags'], 'sources': d['sources'],
        'region': d.get('region', '国内外'), 'layers': d['layers'],
        'issue_no': None, 'pinned': False, 'word_count': cjk,
        'published_at': now_utc.isoformat(), 'body_md': d['body_md'],
    }
    reports.insert(0, entry)
    json.dump({'items': reports}, open(report_path, 'w'), ensure_ascii=False, indent=2)

    det_path = os.path.join(BACKUP, 'article_details', slug + '.json')
    json.dump(entry, open(det_path, 'w'), ensure_ascii=False, indent=2)

    fac_path = os.path.join(BACKUP, 'facets.json')
    facets = json.load(open(fac_path))
    facets['latest']['reports'] = now_utc.isoformat()
    json.dump(facets, open(fac_path, 'w'), ensure_ascii=False, indent=2)

    ov_path = os.path.join(BACKUP, 'overview.json')
    ov = json.load(open(ov_path))
    if not replaced:
        ov['counts']['reports'] += 1
        ov['counts']['articles'] += 1
    ov['latestReports'] = [dict(x) for x in reports[:12]]
    ov.setdefault('runs', []).insert(0, {
        'run_date': today_cst, 'job': 'report', 'status': 'ok', 'added': 1,
        'note': a.note or ('发布深度调研《%s》' % d['title'][:30]),
        'created_at': now_utc.isoformat(),
    })
    json.dump(ov, open(ov_path, 'w'), ensure_ascii=False, indent=2)

    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'regen_api_data.py')],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail('regen failed: %s' % (r.stderr or r.stdout))

    print(json.dumps({
        'created': True, 'replaced': replaced, 'slug': slug,
        'title': d['title'], 'id': art_id, 'chars': bl,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
