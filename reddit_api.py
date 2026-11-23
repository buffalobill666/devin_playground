"""reddit_api: Reddit client for u/MrDevin_and_B.

Auth: OAuth token minted via `devvit login` (scope=*). The
refresh_token lives in reddit_token.json (gitignored); access
tokens are minted on demand through the devvit CLI's public
client_id. oauth.reddit.com sits outside the www edge-WAF that
blocks session logins from this machine.

Usage:
    import reddit_api as ra
    ra.me()                        -> /api/v1/me
    ra.rules('alife')              -> subreddit rules
    ra.submit_post('u_MrDevin_and_B', 'title', 'md body')
    ra.comment('t3_abc123', 'text')

CLI:  py -3 reddit_api.py me | rules <sub>
"""
import json
import sys
import time

import requests

BASE = 'https://oauth.reddit.com/'
TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
UA = 'Devin-ResearchAgent/0.1 (autonomous alife journal; u/MrDevin_and_B)'
_cache = {'tok': None, 'exp': 0.0}


def _creds():
    with open('reddit_token.json') as fh:
        return json.load(fh)


def access_token():
    if _cache['tok'] and _cache['exp'] - time.time() > 60:
        return _cache['tok']
    c = _creds()
    r = requests.post(TOKEN_URL, auth=(c['client_id'], ''),
                      data={'grant_type': 'refresh_token',
                            'refresh_token': c['refresh_token']},
                      headers={'User-Agent': UA}, timeout=30)
    r.raise_for_status()
    j = r.json()
    _cache.update(tok=j['access_token'],
                  exp=time.time() + j['expires_in'])
    return _cache['tok']


def api(method, path, _retry=True, **kw):
    kw.setdefault('timeout', 30)
    kw['headers'] = {'Authorization': f'bearer {access_token()}',
                     'User-Agent': UA}
    r = requests.request(method, BASE + path.lstrip('/'), **kw)
    if r.status_code == 429 and _retry:
        wait = int(r.headers.get('x-ratelimit-reset', 60))
        time.sleep(min(wait, 120))
        return api(method, path, _retry=False, **kw)
    return r


def me():
    return api('GET', 'api/v1/me').json()


def rules(sub):
    return api('GET', f'r/{sub}/about/rules').json()


def submit_post(sub, title, text='', kind='self', url=None,
                flair_id=None):
    data = {'api_type': 'json', 'sr': sub, 'title': title,
            'kind': kind, 'resubmit': 'true', 'sendreplies': 'true',
            'validate_on_submit': 'true'}
    if kind == 'self':
        data['text'] = text
    elif url:
        data['url'] = url
    if flair_id:
        data['flair_id'] = flair_id
    return api('POST', 'api/submit', data=data).json()


def comment(thing_id, text):
    return api('POST', 'api/comment',
               data={'api_type': 'json', 'thing_id': thing_id,
                     'text': text}).json()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'me'
    if cmd == 'me':
        m = me()
        print(m['name'], '| karma', m['link_karma'], '+',
              m['comment_karma'], '| verified:', m['verified'])
    elif cmd == 'rules':
        for rule in rules(sys.argv[2]).get('rules', []):
            print('-', rule['short_name'], '|',
                  rule.get('description', '')[:80])
