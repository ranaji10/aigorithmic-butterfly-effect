#!/usr/bin/env python3
"""The watch: is the sweep still running?

Standard library only; talks to GitHub through the `gh` program that every GitHub runner has.

    python3 tools/watch.py            look, and open or close the alarm
    python3 tools/watch.py --dry      look and say what would be done, change nothing
    WATCH_HOURS=12                    how long without a finished sweep before the alarm (default 12)

The sweep (sweep.yml) is started once an hour by the clock outside GitHub and, as a second clock, by GitHub's own
schedule. If no sweep has FINISHED WELL for WATCH_HOURS hours, marks left at the door are waiting unread and removal
requests are not being honoured, and nobody would notice. Then this opens ONE issue for the stewards (GitHub mails
them). It does not open a second one while the first is open, and it closes its own issue with a line when sweeps
run again. Only an issue written by GitHub's own workflow account counts as the alarm, so a stranger cannot silence
it by opening a look-alike.
"""
import json, os, subprocess, sys
from datetime import datetime, timezone

REPO = os.environ.get('GITHUB_REPOSITORY') or 'ranaji10/aigorithmic-butterfly-effect'
try:
    HOURS = float(os.environ.get('WATCH_HOURS') or 12)
except ValueError:
    HOURS = 12.0
TITLE = 'alarm: no sweep for %g hours' % HOURS
MARK = 'alarm: no sweep'
BOT = 'github-actions[bot]'
DRY = '--dry' in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gh(*args, inp=None):
    r = subprocess.run(['gh', 'api', *args], capture_output=True, text=True, input=inp)
    if r.returncode != 0:
        raise SystemExit('gh api %s failed: %s' % (' '.join(args[:3]), r.stderr.strip()[:300]))
    return json.loads(r.stdout) if r.stdout.strip() else None


def when(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def last_run(**q):
    path = 'repos/%s/actions/workflows/sweep.yml/runs?per_page=1' % REPO
    for k, v in q.items():
        path += '&%s=%s' % (k, v)
    runs = (gh(path) or {}).get('workflow_runs') or []
    return runs[0] if runs else None


def main():
    now = datetime.now(timezone.utc)
    good = last_run(status='success')
    by_clock = last_run(event='workflow_dispatch')
    by_github = last_run(event='schedule')
    latest = last_run()
    age = (now - when(good['updated_at'])).total_seconds() / 3600 if good else float('inf')
    issues = gh('repos/%s/issues?state=open&creator=%s&per_page=100' % (REPO, BOT.replace('[', '%5B').replace(']', '%5D'))) or []
    alarm = next((i for i in issues if 'pull_request' not in i and i['title'].startswith(MARK)
                  and (i.get('user') or {}).get('login') == BOT), None)

    def line(name, run):
        if not run:
            return '- %s: never' % name
        return '- %s: %s, %s' % (name, run['updated_at'].replace('T', ' ').replace('Z', ' UTC'),
                                 run.get('conclusion') or run.get('status'))

    facts = '\n'.join([line('last sweep that finished well', good), line('last sweep of any kind', latest),
                       line('last one started by the outside clock', by_clock),
                       line('last one started by GitHub\'s own schedule', by_github)])
    print('last good sweep %.1f h ago; alarm issue %s' % (age, '#%d open' % alarm['number'] if alarm else 'not open'))
    print(facts)

    if age > HOURS and not alarm:
        body = ('No sweep has finished well for more than %g hours (looked at %s UTC).\n\n%s\n\n'
                'While this lasts, marks left at the door wait unread and removal requests are not honoured.\n\n'
                '**What to do**\n'
                '1. Actions > sweep > Run workflow. If it runs green, the work is safe again and this issue closes by itself.\n'
                '2. If the last sweeps are red, open the newest one and read its log; `python3 tools/wingbeat.py door` is the step that runs.\n'
                '3. If no sweep has been started by the outside clock lately, its token has run out or was revoked: '
                'make a new fine-grained token (this repository only, Actions: read and write) and replace the secret '
                '`GITHUB_TOKEN` of the Cloudflare Worker `abe-sweep-clock` (AGENTS.md, The clock).\n'
                '4. If Actions says the workflow is disabled, press Enable workflow.\n\n'
                'Opened by `tools/watch.py` (workflow `watch`).') % (HOURS, now.strftime('%Y-%m-%d %H:%M'), facts)
        if DRY:
            print('WOULD OPEN:', TITLE); return
        stewards = json.load(open(os.path.join(ROOT, 'data', 'config.json'), encoding='utf-8')).get('stewards') or []
        payload = {'title': TITLE, 'body': body, 'assignees': stewards}
        try:
            made = gh('-X', 'POST', 'repos/%s/issues' % REPO, '--input', '-', inp=json.dumps(payload))
        except SystemExit:
            payload.pop('assignees')            # a steward who cannot be assigned must not cost us the alarm
            made = gh('-X', 'POST', 'repos/%s/issues' % REPO, '--input', '-', inp=json.dumps(payload))
        print('opened #%d' % made['number'])
    elif age <= HOURS and alarm:
        if DRY:
            print('WOULD CLOSE: #%d' % alarm['number']); return
        gh('-X', 'POST', 'repos/%s/issues/%d/comments' % (REPO, alarm['number']), '--input', '-',
           inp=json.dumps({'body': 'Sweeps run again.\n\n' + facts}))
        gh('-X', 'PATCH', 'repos/%s/issues/%d' % (REPO, alarm['number']), '--input', '-',
           inp=json.dumps({'state': 'closed', 'state_reason': 'completed'}))
        print('closed #%d' % alarm['number'])
    else:
        print('nothing to do')


if __name__ == '__main__':
    main()
