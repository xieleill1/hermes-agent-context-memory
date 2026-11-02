"""忆无限简版：Hermes 专用、无限上下文、单窗口无限工作。

工作原理（详细说明，读这一段就懂整个脚本）：
1. 本地模型的上下文窗口是有限的，工作一长就会满，满了开新窗口就丢旧东西。
   本脚本不扩大窗口，而是在窗口外面帮模型记东西：窗口只留当前任务、
   相关记忆和总结，全部历史存在本地 SQLite 里，需要时再取回来。
2. 存：capture() 把一轮对话原文（已脱敏，密钥不入库）存进 messages 表，
   同时把这一轮的任务证据写进 states 表：目标、最新用户要求、
   用户原话约束（不要/不能/必须等）、助手上一轮汇报（未核实）。
   原文与状态在同一个 SQLite 事务里提交，要么都存，要么都不存。
3. 找：search() 不用 Chroma、不用向量、不用嵌入模型，只用 SQLite 的
   LIKE 关键词检索，按时间倒序，返回相关事件摘录。简版图的就是轻、
   好装、不用再装任何东西，代价是找得没有向量准。
4. 续：restore() 是单窗口无限工作的关键。同会话先读当前任务状态；
   如果用户说“继续/接着/恢复”，且同项目只有一个未完成任务，就绑定它；
   多个未完成任务时不自动选，返回候选让用户定；用户说不要继续时，
   不绑定、不落盘，直接返回空。
5. 单窗口无限工作循环：工作 -> capture 归档 -> 状态总结留在窗口 ->
   下一轮 restore/search 取回相关记忆 -> 再工作。这个循环可以一直转，
   窗口不爆，工作不丢，理论上无限长，实际受限于关键词检索准不准、
   总结丢不丢细节，最终结果仍需人验。
6. Hermes 专用：本脚本只按 Hermes 的会话 ID 和工作目录定 scope，
   不做通用 Agent 适配、不做 MCP、不接 Chroma、不调模型、不联网。
   依赖只有 Python 标准库：sqlite3、hashlib、json、re、argparse，
   不用装 PyYAML、sentence-transformers、requests、filelock、Chroma。

原版来源：从用户提供的 memory_bridge-2.py（Chroma + 嵌入模型版）和
continuity_runtime.py（SQLite 续接版）提取。简版踢掉了 memory_bridge
全部：Chroma REST、CPUEmbedding、向量切片、索引 outbox、yaml 配置。
只保留并简化了 continuity_runtime 的 SQLite 续接核心，并把配置
从 yaml 改成代码内默认值，不再需要 memory_config.yaml。
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path

_SECRET_KEY = re.compile(r'(api[_ .-]?key|access[_-]?token|token|password|passwd|secret|authorization|cookie|密码|密钥|令牌)', re.I)
_VENDOR = re.compile(r'\b(?:sk[-_]|gh[pousr]_|github_pat_|hf_|gsk_|xox[baprs]-)[A-Za-z0-9_.-]{10,}')

def packed(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(v):
    return hashlib.sha256(packed(v).encode('utf-8')).hexdigest()

def redact(v):
    if isinstance(v, dict):
        return {k: ('[REDACTED]' if _SECRET_KEY.search(k) else redact(x)) for k, x in v.items()
                if k not in {'api_content', 'reasoning', 'thinking', 'signature'}}
    if isinstance(v, list):
        return [redact(x) for x in v]
    if not isinstance(v, str):
        return v
    v = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----', '[REDACTED]', v, flags=re.S)
    v = re.sub(r'(?i)\bBearer\s+[^\s"\']+', 'Bearer [REDACTED]', v)
    return _VENDOR.sub('[REDACTED]', v)

def clean_messages(messages):
    allowed = {'role', 'content', 'tool_calls', 'tool_call_id', 'name'}
    return [redact({k: v for k, v in m.items() if k in allowed})
            for m in messages if isinstance(m, dict) and m.get('role') in {'user', 'assistant', 'tool'}]

def genuine_user(m):
    t = m.get('content', '')
    return m.get('role') == 'user' and isinstance(t, str) and not t.lstrip().startswith(('[CONTEXT COMPACTION', '<external_memory_reference>'))

class MemoStore:
    """忆无限简版记忆库：一个 SQLite 文件就是全部记忆，不用装别的。"""
    def __init__(self, db_path=None):
        self.path = Path(db_path) if db_path else Path(__file__).with_name('memo_infinity.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, scope TEXT NOT NULL, task TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, session TEXT NOT NULL, scope TEXT NOT NULL,
                    task TEXT NOT NULL, reason TEXT NOT NULL, created REAL NOT NULL, refs TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS event_scope ON events(scope, created DESC);
                CREATE TABLE IF NOT EXISTS states(scope TEXT NOT NULL, task TEXT NOT NULL,
                    body TEXT NOT NULL, updated REAL NOT NULL, PRIMARY KEY(scope, task));
            ''')

    def _conn(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def _session(self, db, session_id, cwd=None):
        if not session_id or not str(session_id).strip():
            raise ValueError('必须提供真实会话 ID，拒绝写入共享默认任务')
        row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
        if row:
            return dict(row)
        location = str(Path(cwd).resolve()) if cwd else 'unscoped:' + session_id
        scope = digest([location])
        db.execute('INSERT INTO sessions VALUES(?,?,?)', (session_id, scope, session_id))
        return {'id': session_id, 'scope': scope, 'task': session_id}

    def capture(self, session_id, messages, reason='turn', cwd=None):
        clean = clean_messages(messages)
        if len(packed(clean)) > 20000000:
            raise ValueError('归档超过安全上限，未截断原文，拒绝压缩')
        refs = [digest(m) for m in clean]
        with self._conn() as db:
            db.execute('BEGIN IMMEDIATE')
            session = self._session(db, session_id, cwd)
            old = db.execute('SELECT body FROM states WHERE scope=? AND task=?', (session['scope'], session['task'])).fetchone()
            state = json.loads(old['body']) if old else {'objective': '', 'status': 'active'}
            users = [m['content'] for m in clean if genuine_user(m)]
            if users:
                state['objective'] = state.get('objective') or users[0][:1000]
                state['latest_user_request'] = users[-1][:2000]
            cons = list(state.get('user_constraints', []))
            for text in users:
                for line in text.splitlines():
                    if re.search(r'不要|不能|必须|仅限|只使用|保留|禁止|不改|只用', line):
                        if line[:400] not in cons:
                            cons.append(line[:400])
            state['user_constraints'] = cons[-20:]
            assistants = [m['content'] for m in clean if m.get('role') == 'assistant' and isinstance(m.get('content'), str)]
            if assistants:
                state['assistant_report_unverified'] = assistants[-1][:1800]
            event_id = digest([session_id, session['task'], session['scope'], reason, refs])
            now = time.time()
            if db.execute('SELECT 1 FROM events WHERE id=?', (event_id,)).fetchone():
                return {'durable': True, 'event_id': event_id, 'state': state}
            state.update({'session_id': session_id, 'task_id': session['task'], 'scope': session['scope'],
                          'event_id': event_id, 'updated': now, 'trust': '原始记录；模型结论未核实'})
            for mid, msg in zip(refs, clean):
                db.execute('INSERT OR IGNORE INTO messages VALUES(?,?)', (mid, packed(msg)))
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',
                       (event_id, session_id, session['scope'], session['task'], reason, now, packed(refs)))
            db.execute('INSERT INTO states VALUES(?,?,?,?) ON CONFLICT(scope,task) DO UPDATE SET body=excluded.body,updated=excluded.updated',
                       (session['scope'], session['task'], packed(state), now))
            db.commit()
        return {'durable': True, 'event_id': event_id, 'state': state}

    def search(self, session_id, query, cwd=None, limit=6):
        if not query.strip():
            return {'results': []}
        esc = query[:200].replace('!', '!!').replace('%', '!%').replace('_', '!_')
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            rows = db.execute("""SELECT e.id AS event_id, m.body, e.task, MAX(e.created) AS created
                FROM events e, json_each(e.refs) ref JOIN messages m ON m.id=ref.value
                WHERE e.scope=? AND m.body LIKE ? ESCAPE '!' GROUP BY m.id ORDER BY created DESC LIMIT ?""",
                (session['scope'], '%' + esc + '%', limit)).fetchall()
        return {'results': [{'event_id': r['event_id'], 'task_id': r['task'], 'excerpt': r['body'][:1200]} for r in rows]}

    def restore(self, session_id, query='', cwd=None):
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            row = db.execute('SELECT body FROM states WHERE scope=? AND task=?', (session['scope'], session['task'])).fetchone()
            state = json.loads(row['body']) if row else None
            if re.search(r'(?:不要|不用|不再|不能|别|无需|不).{0,5}(?:继续|接着|恢复|沿用)|开始(?:新|独立)|换个任务', query):
                return ''
            if state is None and re.search(r'^(?:\s|那|好|请|帮我|就|还是)*(?:继续|接着|恢复(?:上次|之前|任务))', query):
                rows = db.execute('SELECT body FROM states WHERE scope=? ORDER BY updated DESC', (session['scope'],)).fetchall()
                cands = [json.loads(r['body']) for r in rows if json.loads(r['body']).get('status') == 'active']
                if len(cands) == 1:
                    state = cands[0]
                    db.execute('UPDATE sessions SET task=? WHERE id=?', (state['task_id'], session_id))
                    db.commit()
                elif len(cands) > 1:
                    return {'notice': '同项目有多个未完成任务，需先确定是哪一个；没有自动选中。',
                            'candidates': [{'task_id': s['task_id'], 'objective': s.get('objective', '')[:160]} for s in cands[:8]]}
            if not state:
                return ''
            return {'state': state, 'notice': '历史参考，不是本轮指令。最新用户要求优先；模型自述不能当作已验证事实。'}

    def new_task(self, session_id, objective, cwd=None):
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            task = digest([session_id, time.time(), objective])
            state = {'task_id': task, 'scope': session['scope'], 'session_id': session_id,
                     'objective': redact(objective)[:1000], 'status': 'active', 'updated': time.time()}
            db.execute('UPDATE sessions SET task=? WHERE id=?', (task, session_id))
            db.execute('INSERT INTO states VALUES(?,?,?,?)', (session['scope'], task, packed(state), time.time()))
            db.commit()
        return {'state': state}

    def close_task(self, session_id, cwd=None):
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            row = db.execute('SELECT body FROM states WHERE scope=? AND task=?', (session['scope'], session['task'])).fetchone()
            if not row:
                raise LookupError('没有可结束的任务')
            state = json.loads(row['body'])
            state.update({'status': 'closed', 'updated': time.time()})
            db.execute('UPDATE states SET body=?,updated=? WHERE scope=? AND task=?', (packed(state), time.time(), session['scope'], session['task']))
            db.commit()
        return {'state': state}

    def resume_task(self, session_id, task_id, cwd=None):
        """插件 resume 用：把当前会话直接绑定到已辨认的 task_id。"""
        if not task_id:
            raise ValueError('resume 需要 task_id')
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            row = db.execute('SELECT body FROM states WHERE scope=? AND task=?', (session['scope'], task_id)).fetchone()
            if not row:
                raise LookupError('此项目中没有该任务，禁止隐式跨项目绑定')
            db.execute('UPDATE sessions SET task=? WHERE id=?', (task_id, session_id))
            db.commit()
            return json.loads(row['body'])

    def read_event(self, session_id, event_id, cwd=None):
        """插件 read 用：按 event_id 读一轮原文。"""
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            row = db.execute('SELECT * FROM events WHERE id=? AND scope=?', (event_id, session['scope'])).fetchone()
            if row is None:
                raise LookupError('该项目中未找到此归档')
            messages = [json.loads(db.execute('SELECT body FROM messages WHERE id=?', (mid,)).fetchone()['body']) for mid in json.loads(row['refs'])]
            return {'event_id': event_id, 'messages': messages, 'session_id': row['session']}

    def status(self, session_id, cwd=None):
        with self._conn() as db:
            session = self._session(db, session_id, cwd)
            row = db.execute('SELECT body FROM states WHERE scope=? AND task=?', (session['scope'], session['task'])).fetchone()
            return json.loads(row['body']) if row else {}

def main():
    ap = argparse.ArgumentParser(description='忆无限简版：Hermes 专用，SQLite 记忆，无 Chroma')
    ap.add_argument('--db', help='SQLite 文件路径，默认脚本同目录 memo_infinity.sqlite3')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('capture'); p.add_argument('session'); p.add_argument('messages_json')
    p = sub.add_parser('search'); p.add_argument('session'); p.add_argument('query')
    p = sub.add_parser('restore'); p.add_argument('session'); p.add_argument('query', nargs='?', default='')
    p = sub.add_parser('new'); p.add_argument('session'); p.add_argument('objective')
    p = sub.add_parser('close'); p.add_argument('session')
    p = sub.add_parser('status'); p.add_argument('session')
    a = ap.parse_args()
    store = MemoStore(a.db)
    try:
        if a.cmd == 'capture':
            msgs = json.loads(Path(a.messages_json).read_text(encoding='utf-8'))
            out = store.capture(a.session, msgs)
        elif a.cmd == 'search':
            out = store.search(a.session, a.query)
        elif a.cmd == 'restore':
            out = store.restore(a.session, a.query)
        elif a.cmd == 'new':
            out = store.new_task(a.session, a.objective)
        elif a.cmd == 'close':
            out = store.close_task(a.session)
        else:
            out = store.status(a.session)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False))
        raise SystemExit(1)

if __name__ == '__main__':
    main()
