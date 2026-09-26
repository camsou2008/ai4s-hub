#!/usr/bin/env python3
"""Append new signal items to the local AI4S dataset, refresh derived fields
(facets.json / overview.json), and regenerate api-data.js.

Usage:
    python3 tools/add_signals.py /tmp/new_signals.json --note "一句话说明"

/tmp/new_signals.json format: {"items": [ {org, layer, region, summary,
occurred_on, source_title, source_site, source_url, primary_src}, ... ]}

Prints a JSON report: {created, skipped_duplicate, rejected, total_signals}.
Exit 0 even when some items are rejected (details in report); exit 2 on
fatal errors (bad input file etc.).
"""
import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser('~')
BACKUP = os.path.join(HOME, 'workspace/publish/ai4s_api_backup')
TOOLS = os.path.join(HOME, 'workspace/publish/ai4s/tools')
LAYERS = {'compute', 'model', 'data', 'tools', 'org', 'region'}
REQUIRED = ['org', 'layer', 'region', 'summary', 'occurred_on',
            'source_title', 'source_site', 'source_url']

CST = timezone(timedelta(hours=8))
now_utc = datetime.now(timezone.utc)
today_cst = datetime.now(CST).date()
min_date = (today_cst - timedelta(days=2)).isoformat()
max_date = today_cst.isoformat()


def ingest_day(s):
    ca = s.get('collected_at') or ''
    try:
        dt = datetime.fromisoformat(ca)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(CST).date().isoformat()
    except Exception:
        return s.get('occurred_on', '')


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
        raw = json.load(open(a.input))
    except Exception as e:
        fail('cannot read input: %s' % e)
    items = raw.get('items', raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        fail('input must be a list or {"items": [...]}')

    sig_path = os.path.join(BACKUP, 'signals.json')
    signals = json.load(open(sig_path))['items']
    seen_urls = {s.get('source_url') for s in signals}
    seen_org_title = {(s.get('org'), s.get('source_title')) for s in signals}
    next_id = max([s.get('id', 0) for s in signals] + [0])

    created, skipped, rejected = [], 0, []

    for it in items:
        # required fields
        missing = [k for k in REQUIRED if not it.get(k)]
        if missing:
            rejected.append({'item': {k: it.get(k) for k in ('org', 'source_title')},
                             'reason': 'missing fields: %s' % ','.join(missing)})
            continue
        if it['layer'] not in LAYERS:
            rejected.append({'item': {'org': it['org']}, 'reason': 'bad layer'})
            continue
        d = it['occurred_on']
        if not (min_date <= d <= max_date):
            rejected.append({'item': {'org': it['org']},
                             'reason': 'occurred_on_out_of_window (%s not in %s..%s)' % (d, min_date, max_date)})
            continue
        ln = len(it['summary'])
        if ln < 40 or ln > 200:
            rejected.append({'item': {'org': it['org']},
                             'reason': 'summary length %d out of 40..200' % ln})
            continue
        if it['source_url'] in seen_urls or (it['org'], it['source_title']) in seen_org_title:
            skipped += 1
            continue
        next_id += 1
        created.append({
            'id': next_id,
            'org': it['org'],
            'layer': it['layer'],
            'region': it['region'],
            'summary': it['summary'],
            'occurred_on': d,
            'source_title': it['source_title'],
            'source_site': it['source_site'],
            'source_url': it['source_url'],
            'primary_src': bool(it.get('primary_src', False)),
            'daily_slug': it.get('daily_slug'),
            'collected_at': now_utc.isoformat(),
        })
        seen_urls.add(it['source_url'])
        seen_org_title.add((it['org'], it['source_title']))

    signals = created + signals
    signals.sort(key=lambda s: (s.get('collected_at', ''), s.get('occurred_on', '')), reverse=True)
    json.dump({'items': signals}, open(sig_path, 'w'), ensure_ascii=False, indent=2)

    # facets.json: refresh signalsPerDay + latest.signals
    fac_path = os.path.join(BACKUP, 'facets.json')
    facets = json.load(open(fac_path))
    per_day = {}
    for s in signals:
        d = ingest_day(s)
        per_day[d] = per_day.get(d, 0) + 1
    facets['signalsPerDay'] = [{'day': d, 'total': per_day[d]}
                               for d in sorted(per_day, reverse=True)[:30]]
    facets['latest']['signals'] = now_utc.isoformat()
    json.dump(facets, open(fac_path, 'w'), ensure_ascii=False, indent=2)

    # overview.json: counts, embedded signals, run log
    ov_path = os.path.join(BACKUP, 'overview.json')
    ov = json.load(open(ov_path))
    ov['counts']['signals'] = len(signals)
    ov['signals'] = signals
    ov.setdefault('runs', []).insert(0, {
        'run_date': max_date,
        'job': 'signal',
        'status': 'ok',
        'added': len(created),
        'note': a.note or ('新增 %d 条' % len(created)),
        'created_at': now_utc.isoformat(),
    })
    json.dump(ov, open(ov_path, 'w'), ensure_ascii=False, indent=2)

    # regenerate api-data.js
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'regen_api_data.py')],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail('regen failed: %s' % (r.stderr or r.stdout))

    print(json.dumps({
        'created': len(created),
        'skipped_duplicate': skipped,
        'rejected': rejected,
        'total_signals': len(signals),
        'added_orgs': [{'org': c['org'], 'summary': c['summary']} for c in created],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
