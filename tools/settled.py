#!/usr/bin/env python3
"""Settled: close the stewards' issue once everything it asked has been decided.

Standard library only; talks to GitHub through the `gh` program that every GitHub runner has.

    python3 tools/settled.py            look, and close what is settled
    python3 tools/settled.py --dry      look and say what would be done, change nothing
    python3 tools/settled.py --dry --closed     the same over the closed issues too (a rehearsal against the past)

The sweep opens an issue titled "for the stewards, <day>" when a person has to decide something: somebody pressed
"This is me" on a name, or asked for something to be removed. The steward decides (an issue titled `confirm p-name` or
`deny p-name`, or `python3 tools/wingbeat.py resolve N removed|restored`), and until 22 November 2026 the issue that
asked stayed open until somebody closed it by hand. This reads each open issue of that kind and closes it, with one
comment that says what was decided, when every line in it that asked for a decision has one:

    "... was claimed on the site (`p-name`, ..."    settled when people/p-name.json holds no `pending` any more
    "removal request x00012: ..."                   settled when removals/x00012.json is `removed` or `restored`

Lines that only tell ("claimed their own presence", "was asked for at the door ... Nothing needs doing") neither keep
an issue open nor close one. Any other line (the call paused itself, the sweep took a mark back, a flood of
requests) is something a person should read: an issue that holds one is never closed here. An issue with no line
that asked for a decision is left alone too.

Only an issue written by GitHub's own workflow account counts, so a stranger's look-alike is neither read nor closed.
What an issue says is never run and never trusted: the names and numbers in it are only looked up in this
repository's own files, which say what was decided. It decides nothing itself.
"""
import json, os, re, subprocess, sys

REPO = os.environ.get('GITHUB_REPOSITORY') or 'ranaji10/aigorithmic-butterfly-effect'
BOT = 'github-actions[bot]'
MARK = 'for the stewards, '
DRY = '--dry' in sys.argv
PAST = '--closed' in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLAIM = re.compile(r'^- \*\*.{1,80}?\*\* was claimed on the site \(`(p-[a-z0-9-]{1,44})`')
REMOVAL = re.compile(r'^- removal request x(\d{5}): ')
TELLS = (re.compile(r'^- .{1,80}? claimed their own presence \(p-[a-z0-9-]{1,44}\)$'),
         re.compile(r'^- \*\*.{1,80}?\*\* was asked for at the door \(`p-[a-z0-9-]{1,44}`\), but .* Nothing needs doing\.$'))


def gh(*args, inp=None):
    r = subprocess.run(['gh', 'api', *args], capture_output=True, text=True, input=inp)
    if r.returncode != 0:
        raise SystemExit('gh api %s failed: %s' % (' '.join(args[:3]), r.stderr.strip()[:300]))
    return json.loads(r.stdout) if r.stdout.strip() else None


def load(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def claim(pid):
    """(settled?, what to say) for a request for a name."""
    p = load('people/%s.json' % pid)
    if p is None:
        return True, '`%s`: no longer listed.' % pid
    if p.get('pending'):
        return False, '`%s`: still waiting for a steward.' % pid
    if p.get('claimed'):
        return True, '`%s`: confirmed%s.' % (pid, ', the name is held since %s' % p['since'] if p.get('since') else '')
    return True, '`%s`: nobody is waiting for this name any more (refused, or taken back).' % pid


def removal(n):
    x = load('removals/x%s.json' % n)
    if x is None:
        return False, 'x%s: its file was not found.' % n
    if x.get('state') in ('removed', 'restored'):
        return True, 'x%s (`%s`): settled as %s%s.' % (n, x.get('id'), x['state'],
                                                       ' on %s' % x['resolved_at'] if x.get('resolved_at') else '')
    return False, 'x%s (`%s`): still waiting for a steward.' % (n, x.get('id'))


def read(body):
    """An issue's lines: (asked, all settled?, a person should read it?, what to say)."""
    asked, done, other, words = 0, True, False, []
    for line in (body or '').replace('\r', '').split('\n'):
        if not line.startswith('- '):
            continue
        m, r = CLAIM.match(line), REMOVAL.match(line)
        if m or r:
            ok, say = claim(m.group(1)) if m else removal(r.group(1))
            asked += 1
            done = done and ok
            words.append('- ' + say)
        elif not any(t.match(line) for t in TELLS):
            other = True
    return asked, done, other, words


def main():
    who = BOT.replace('[', '%5B').replace(']', '%5D')
    issues = gh('repos/%s/issues?state=%s&creator=%s&per_page=100' % (REPO, 'all' if PAST and DRY else 'open', who)) or []
    closed = 0
    for i in issues:
        if 'pull_request' in i or (i.get('user') or {}).get('login') != BOT or not (i.get('title') or '').startswith(MARK):
            continue
        asked, done, other, words = read(i.get('body'))
        if not asked:
            print('#%d: asks for no decision; left alone' % i['number'])
            continue
        if other:
            print('#%d: holds a line a person should read; left open' % i['number'])
            continue
        if not done:
            print('#%d: waits\n%s' % (i['number'], '\n'.join(words)))
            continue
        say = ('Everything this issue asked about has been decided, so it is closed.\n\n%s\n\n'
               'Closed by `tools/settled.py`, which decides nothing: it reads what the stewards decided.' % '\n'.join(words))
        if DRY:
            print('#%d: WOULD CLOSE\n%s' % (i['number'], '\n'.join(words)))
            continue
        gh('-X', 'POST', 'repos/%s/issues/%d/comments' % (REPO, i['number']), '--input', '-', inp=json.dumps({'body': say}))
        gh('-X', 'PATCH', 'repos/%s/issues/%d' % (REPO, i['number']), '--input', '-',
           inp=json.dumps({'state': 'closed', 'state_reason': 'completed'}))
        closed += 1
        print('#%d: closed\n%s' % (i['number'], '\n'.join(words)))
    print('closed %d' % closed if not DRY else 'dry run: nothing changed')


if __name__ == '__main__':
    main()
