#!/usr/bin/env python3
"""Look after the door's one dependency without a person having to remember it.

    python3 tools/dependencies.py judge     try every open Dependabot pull request; print and output a verdict for each
    python3 tools/dependencies.py settle    merge the ones judged safe, say why on the others (reads VERDICTS)

Run by .github/workflows/dependencies.yml once a day. Standard library only; it calls `git`, `npm`, `node` and `gh`.

A pull request is merged only if ALL of this holds:
  1. it comes from Dependabot and changes nothing but door/package.json and door/package-lock.json;
  2. it does not make things worse: no more known advisories than `main` has (and no more high or critical ones),
     and the tree of packages does not grow beyond twice its size (the door is meant to stay small enough to read);
  3. every package version it brings in has been public for at least SETTLE_DAYS days (bad releases are usually
     withdrawn within days);
  4. the door still works with it: tools/door_check.mjs passes (storage calls against a stand-in, and a full rehearsal).
Otherwise it is left open with one comment that says which rule stopped it, for a steward to read.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {'door/package.json', 'door/package-lock.json'}
SETTLE_DAYS = 7
MARK = '<!-- dependencies-check %s -->'


def sh(cmd, cwd=None, env=None, timeout=600):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def measure(door):
    """(installed ok, {severity: count}, number of packages, {name: version}) for a door/ folder."""
    rc, _, err = sh(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], cwd=door)
    if rc:
        return False, {}, 0, {}, err[-300:]
    _, out, _ = sh(['npm', 'audit', '--json'], cwd=door)
    try:
        sev = json.loads(out)['metadata']['vulnerabilities']
    except Exception:
        return False, {}, 0, {}, 'npm audit gave no answer'
    lock = json.load(open(os.path.join(door, 'package-lock.json')))
    pk = {k.split('node_modules/')[-1]: v.get('version', '') for k, v in lock.get('packages', {}).items() if k}
    return True, sev, len(pk), pk, ''


def age_days(name, version):
    rc, out, _ = sh(['npm', 'view', '%s@%s' % (name, version), 'time', '--json'])
    try:
        t = json.loads(out)[version]
        then = datetime.datetime.fromisoformat(t.replace('Z', '+00:00'))
        return (datetime.datetime.now(datetime.timezone.utc) - then).days
    except Exception:
        return -1


def judge():
    rc, out, err = sh(['gh', 'pr', 'list', '--state', 'open', '--author', 'app/dependabot', '--limit', '20',
                       '--json', 'number,headRefOid,files,isCrossRepository'], cwd=ROOT)
    if rc:
        print('could not list pull requests:', err[-300:])
        return 1
    prs = json.loads(out or '[]')
    verdicts = []
    base = None
    for pr in prs:
        n, sha = pr['number'], pr['headRefOid']
        v = {'n': n, 'sha': sha, 'ok': False, 'why': []}
        verdicts.append(v)
        files = {f['path'] for f in pr.get('files', [])}
        if pr.get('isCrossRepository') or not files or not files <= ALLOWED:
            v['why'].append('it changes more than the door\'s two dependency files (%s); a steward has to read it.' % ', '.join(sorted(files - ALLOWED)[:5]))
            continue
        if base is None:
            base = measure(os.path.join(ROOT, 'door'))
        if not base[0]:
            v['why'].append('`main` itself does not install (%s); nothing can be compared.' % base[4])
            continue
        tmp = tempfile.mkdtemp(prefix='pr%d-' % n)
        rc, _, err = sh(['git', 'fetch', '--quiet', '--depth', '1', 'origin', 'pull/%d/head' % n], cwd=ROOT)
        rc2, _, err2 = sh(['git', 'worktree', 'add', '--detach', tmp, sha], cwd=ROOT)
        if rc or rc2:
            v['why'].append('its commit could not be fetched (%s).' % (err + err2)[-200:])
            continue
        ok, sev, count, pk, err = measure(os.path.join(tmp, 'door'))
        if not ok:
            v['why'].append('it does not install: %s' % err)
            continue
        b_sev, b_count, b_pk = base[1], base[2], base[3]
        total, b_total = sev.get('total', 0), b_sev.get('total', 0)
        grave, b_grave = sev.get('high', 0) + sev.get('critical', 0), b_sev.get('high', 0) + b_sev.get('critical', 0)
        if total > b_total or grave > b_grave:
            v['why'].append('it has more known advisories than `main`: %d (%d high or critical) against %d (%d).' % (total, grave, b_total, b_grave))
        if count > max(2 * b_count, b_count + 5):
            v['why'].append('it grows the door from %d packages to %d.' % (b_count, count))
        changed = sorted((k, ver) for k, ver in pk.items() if b_pk.get(k) != ver)
        if len(changed) > 40:
            v['why'].append('it changes %d packages at once.' % len(changed))
        else:
            young = [(k, ver, d) for k, ver in changed for d in [age_days(k, ver)] if d < SETTLE_DAYS]
            if young:
                v['why'].append('some versions are younger than %d days or their age is unknown: %s. It will be looked at again tomorrow.' % (
                    SETTLE_DAYS, ', '.join('%s %s' % (k, ver) for k, ver, _ in young[:6])))
        if not v['why']:
            env = dict(os.environ, ABE_CHECK_ROOT=tmp)
            for k in ('GH_TOKEN', 'GITHUB_TOKEN'):
                env.pop(k, None)             # the code under test gets no token
            rc, out, err = sh(['node', os.path.join(ROOT, 'tools', 'door_check.mjs')], cwd=tmp, env=env, timeout=300)
            if rc:
                fails = [l for l in out.splitlines() if l.startswith('FAIL')]
                v['why'].append('the door does not pass its check with it: %s' % ('; '.join(fails)[:400] or err[-200:]))
        v['ok'] = not v['why']
        v['note'] = 'advisories %d -> %d, packages %d -> %d, %d versions changed' % (b_total, total, b_count, count, len(changed))
        print('#%d %s: %s %s' % (n, sha[:7], 'SAFE TO MERGE' if v['ok'] else 'left open', v['note']))
        for w in v['why']:
            print('   ' + w)
    if not prs:
        print('No open Dependabot pull requests.')
    line = json.dumps(verdicts)
    if os.environ.get('GITHUB_OUTPUT'):
        open(os.environ['GITHUB_OUTPUT'], 'a').write('verdicts=%s\n' % line)
    else:
        print(line)
    return 0


def settle():
    repo = os.environ['GITHUB_REPOSITORY']
    for v in json.loads(os.environ.get('VERDICTS') or '[]'):
        n, sha = int(v['n']), str(v['sha'])
        if v.get('ok') is True:
            rc, out, err = sh(['gh', 'api', '-X', 'PUT', 'repos/%s/pulls/%d/merge' % (repo, n), '-f', 'sha=' + sha, '-f', 'merge_method=squash',
                               '-f', 'commit_title=door: dependency update (#%d), checked by the daily dependencies run' % n])
            print('#%d merged' % n if not rc else '#%d could not be merged: %s' % (n, (out + err)[-300:]))
            continue
        mark = MARK % sha
        rc, out, _ = sh(['gh', 'api', 'repos/%s/issues/%d/comments' % (repo, n), '--paginate', '--jq', '.[].body'])
        if mark in out:
            print('#%d already has its note' % n)
            continue
        body = ('The daily dependencies run tried this update and did not merge it:\n\n%s\n\n%s\n\nA steward can merge it by hand after reading it, '
                'or close it. The rules are at the top of `tools/dependencies.py`.\n%s') % (
            '\n'.join('- ' + str(w)[:600] for w in v.get('why', [])[:8]), str(v.get('note', ''))[:200], mark)
        rc, out, err = sh(['gh', 'api', '-X', 'POST', 'repos/%s/issues/%d/comments' % (repo, n), '-f', 'body=' + body])
        print('#%d noted' % n if not rc else '#%d could not be noted: %s' % (n, (out + err)[-300:]))
    return 0


if __name__ == '__main__':
    sys.exit({'judge': judge, 'settle': settle}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: print(__doc__) or 2)())
