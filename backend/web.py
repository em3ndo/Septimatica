"""Authenticated application API. No unauthenticated legacy analysis routes."""
import hashlib
import json
import os
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from starlette.middleware.sessions import SessionMiddleware
import networkx as nx

from .analysis import TOPICS, analyze
from .models import GraphData
from .proofs import certificate
from .storage import db
from .tutor import feedback
from .limits import BodyLimit

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
app = FastAPI(title='Septimatica', docs_url=None, redoc_url=None)
secret = os.getenv('SESSION_SECRET')
production = os.getenv('APP_ENV') == 'production'
if production and (not secret or len(secret) < 32):
    raise RuntimeError('Production requires a random SESSION_SECRET of at least 32 characters.')
app.add_middleware(SessionMiddleware, secret_key=secret or secrets.token_hex(32),
                   https_only=production, same_site='lax', max_age=600)
app.add_middleware(BodyLimit)
oauth = OAuth()
issuer = os.getenv('OIDC_ISSUER', '').rstrip('/')
sso_ready = bool(issuer and os.getenv('OIDC_CLIENT_ID') and os.getenv('OIDC_CLIENT_SECRET'))
if issuer:
    if not issuer.startswith('https://'):
        raise RuntimeError('OIDC_ISSUER must use HTTPS.')
    oauth.register('school', client_id=os.getenv('OIDC_CLIENT_ID'), client_secret=os.getenv('OIDC_CLIENT_SECRET'),
                   server_metadata_url=issuer+'/.well-known/openid-configuration',
                   client_kwargs={'scope': 'openid email profile', 'code_challenge_method': 'S256'})
rates = defaultdict(deque)


@app.middleware('http')
async def browser_security(request, call_next):
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.headers.get('x-septimatica') != '1':
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail': 'Missing same-origin request header.'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store'
    return response


def current_user(request: Request):
    token = request.cookies.get('septimatica_auth', '')
    digest = hashlib.sha256(token.encode()).hexdigest()
    with db() as conn:
        row = conn.execute('SELECT users.id,users.email FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?',
                           (digest, time.time())).fetchone()
    if not row:
        raise HTTPException(401, 'Sign in to continue.')
    user = dict(row)
    user['instructor'] = user['email'] in {email.strip() for email in os.getenv('INSTRUCTOR_EMAILS', '').lower().split(',')}
    return user


def instructor(user=Depends(current_user)):
    if not user['instructor']:
        raise HTTPException(403, 'Instructor access required.')
    return user


def login_response(user_id, email):
    token = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute('INSERT OR REPLACE INTO users VALUES (?,?)', (user_id, email))
        conn.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
        conn.execute('INSERT INTO sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, time.time()+28800))
    response = RedirectResponse('/', status_code=303)
    response.set_cookie('septimatica_auth', token, httponly=True, secure=production, samesite='lax', max_age=28800)
    return response


@app.get('/api/config')
def config():
    return {'sso_configured': sso_ready, 'demo_available': not production and os.getenv('ALLOW_DEMO_LOGIN') == 'true',
            'gemini_configured': bool(os.getenv('GEMINI_API_KEY')), 'course_url': 'https://math.hmc.edu/su/math55/'}


@app.get('/api/me')
def me(user=Depends(current_user)):
    return user


@app.get('/api/auth/login')
async def login(request: Request):
    if not sso_ready:
        raise HTTPException(503, 'HMC SSO needs an institution-registered OIDC application. See setup documentation.')
    callback = os.getenv('OIDC_REDIRECT_URI')
    if not callback:
        raise HTTPException(503, 'OIDC_REDIRECT_URI must be configured.')
    return await oauth.school.authorize_redirect(request, callback)


@app.get('/api/auth/callback')
async def callback(request: Request):
    if not sso_ready:
        raise HTTPException(503, 'SSO not configured.')
    try:
        token = await oauth.school.authorize_access_token(request)
        info = token.get('userinfo', {})
        email = info.get('email', '').lower()
        allowed = os.getenv('ALLOWED_EMAIL_DOMAINS', 'hmc.edu,g.hmc.edu').split(',')
        if info.get('iss') != issuer or info.get('email_verified') is not True or email.rsplit('@', 1)[-1] not in allowed or not info.get('sub'):
            raise ValueError
    except Exception:
        raise HTTPException(403, 'School identity could not be verified. Contact your administrator.') from None
    request.session.clear()
    return login_response(issuer+'|'+info['sub'], email)


@app.post('/api/auth/demo')
def demo():
    if production or os.getenv('ALLOW_DEMO_LOGIN') != 'true':
        raise HTTPException(403, 'Demo sign-in is disabled.')
    return login_response('demo-'+uuid.uuid4().hex, 'demo@localhost')


@app.post('/api/auth/logout')
def logout(request: Request):
    with db() as conn:
        conn.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(request.cookies.get('septimatica_auth', '').encode()).hexdigest(),))
    response = RedirectResponse('/', status_code=303)
    response.delete_cookie('septimatica_auth')
    request.session.clear()
    return response


class Policy(BaseModel):
    released: list[Literal['coloring','planarity','bipartite','connectivity','eulerian']] = Field(default_factory=list)
    release_at: dict[str, datetime] = Field(default_factory=dict)
    protected_graphs: list[GraphData] = Field(default_factory=list, max_length=12)
    require_proof: bool = True

    @model_validator(mode='after')
    def dates(self):
        if any(k not in TOPICS or v.tzinfo is None for k, v in self.release_at.items()):
            raise ValueError('Release dates require known topics and timezone offsets.')
        return self


def policy():
    with db() as conn:
        row = conn.execute('SELECT data FROM policy WHERE id=1').fetchone()
    return Policy.model_validate_json(row['data']) if row else Policy()


def protected(graph, p):
    # Degree sequence prefilter and VF2++ handle relabeling and repositioning.
    return any(nx.vf2pp_is_isomorphic(graph.nx(), other.nx()) for other in p.protected_graphs)


def permissions(graph, user):
    if not production and os.getenv('ALLOW_DEMO_LOGIN') == 'true' and user['id'].startswith('demo-'):
        return {t: {'allowed': True, 'reason': 'Local practice mode; not an institutional account.'} for t in TOPICS}
    p = policy()
    blocked = protected(graph, p)
    with db() as conn:
        grants = {r['topic'] for r in conn.execute('SELECT topic FROM grants WHERE owner=? AND fingerprint=?', (user['id'], graph.fingerprint()))}
    released = set(p.released) | {k for k, v in p.release_at.items() if v <= datetime.now(timezone.utc)}
    return {t: {'allowed': user['instructor'] or (not blocked and t in released and (not p.require_proof or t in grants)),
                'reason': 'Protected assignment graph: ask your instructor.' if blocked else
                          'This topic has not been released by your instructor.' if t not in released else
                          'Show your reasoning and submit a certificate or request instructor review.' if p.require_proof and t not in grants else 'Available'} for t in TOPICS}


@app.post('/api/access')
def access(graph: GraphData, user=Depends(current_user)):
    return permissions(graph, user)


class AnalysisRequest(BaseModel):
    graph: GraphData
    topic: Literal['coloring','planarity','bipartite','connectivity','eulerian']


@app.post('/api/analyze')
def analysis(req: AnalysisRequest, user=Depends(current_user)):
    access = permissions(req.graph, user)[req.topic]
    if not access['allowed']:
        raise HTTPException(403, access['reason'])
    return analyze(req.graph.nx(), req.topic)


class LayoutRequest(BaseModel):
    graph: GraphData
    method: Literal['spring','circular','spectral'] = 'spring'


@app.post('/api/layout')
def layout(req: LayoutRequest, user=Depends(current_user)):
    g = req.graph.nx()
    fn = {'spring': nx.spring_layout, 'circular': nx.circular_layout, 'spectral': nx.spectral_layout}[req.method]
    positions = fn(g, **({'seed': 42} if req.method == 'spring' else {}))
    return {n: {'x': 400+float(p[0])*330, 'y': 260+float(p[1])*200} for n, p in positions.items()}


class SaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    graph: GraphData


@app.get('/api/graphs')
def graphs(user=Depends(current_user)):
    with db() as conn:
        return [dict(r) | {'graph': json.loads(r['data'])} for r in conn.execute('SELECT id,name,data FROM graphs WHERE owner=?', (user['id'],))]


@app.post('/api/graphs')
def save(req: SaveRequest, user=Depends(current_user)):
    graph_id = uuid.uuid4().hex
    with db() as conn:
        if conn.execute('SELECT count(*) FROM graphs WHERE owner=?', (user['id'],)).fetchone()[0] >= 100:
            raise HTTPException(409, 'Notebook limit reached. Delete a saved graph first.')
        conn.execute('INSERT INTO graphs VALUES (?,?,?,?)', (graph_id, user['id'], req.name, req.graph.model_dump_json()))
    return {'id': graph_id}


@app.delete('/api/graphs/{graph_id}')
def delete_graph(graph_id: str, user=Depends(current_user)):
    with db() as conn:
        conn.execute('DELETE FROM graphs WHERE id=? AND owner=?', (graph_id, user['id']))
    return {'ok': True}


class ProofRequest(AnalysisRequest):
    proof: str = Field(min_length=15, max_length=6000)
    witness: dict = Field(default_factory=dict)


@app.post('/api/proofs')
def proof(req: ProofRequest, user=Depends(current_user)):
    p = policy()
    if protected(req.graph, p) and not user['instructor']:
        raise HTTPException(403, 'Protected assignment: proof checking is disabled. Ask your instructor.')
    result = certificate(req.graph.nx(), req.topic, req.witness)
    sid = uuid.uuid4().hex
    with db() as conn:
        conn.execute('INSERT INTO submissions VALUES (?,?,?,?,?,?)', (sid, user['id'], req.graph.fingerprint(), req.topic,
                     json.dumps({'text': req.proof, 'graph': req.graph.model_dump(), 'evidence': result}), 'verified' if result['valid'] and req.topic != 'coloring' else 'pending'))
        # A proper coloring alone establishes only an upper bound, not minimality.
        if result['valid'] and req.topic != 'coloring':
            conn.execute('INSERT OR IGNORE INTO grants VALUES (?,?,?)', (user['id'], req.graph.fingerprint(), req.topic))
    return result | {'submission_id': sid, 'note': 'Certificate validity does not verify your prose. Course release rules still apply.'}


class Message(BaseModel):
    role: Literal['user','assistant']
    text: str = Field(max_length=6000)


class ChatRequest(BaseModel):
    graph: GraphData
    message: str = Field(min_length=1, max_length=6000)
    history: list[Message] = Field(default_factory=list, max_length=12)
    assigned_work: bool = False


@app.post('/api/chat')
async def chat(req: ChatRequest, user=Depends(current_user)):
    if req.assigned_work or protected(req.graph, policy()):
        return {'feedback': 'For assigned work, please discuss your reasoning with your instructor or peers. We can explore a different practice example together.', 'verdict': 'uncertain', 'verification': 'Course policy'}
    now = time.monotonic()
    queue = rates[user['id']]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= 8:
        raise HTTPException(429, 'Take a moment to think; try another question in a minute.')
    queue.append(now)
    # Do not give the LLM hidden answers for locked topics.
    rights = permissions(req.graph, user)
    facts = {t: analyze(req.graph.nx(), t) for t in TOPICS if rights[t]['allowed']}
    with db() as conn:
        rows = conn.execute('SELECT proof FROM submissions WHERE owner=? AND fingerprint=? ORDER BY rowid DESC LIMIT 3',
                            (user['id'], req.graph.fingerprint())).fetchall()
    facts['student_certificates'] = [json.loads(row['proof'])['evidence'] for row in rows]
    return await feedback(req.graph.model_dump(), req.message, [m.model_dump() for m in req.history], facts)


@app.get('/api/instructor/policy')
def read_policy(user=Depends(instructor)):
    return policy()


@app.put('/api/instructor/policy')
def set_policy(value: Policy, user=Depends(instructor)):
    with db() as conn:
        conn.execute('INSERT OR REPLACE INTO policy VALUES (1,?)', (value.model_dump_json(),))
    return value


@app.get('/api/instructor/submissions')
def submissions(user=Depends(instructor)):
    with db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM submissions WHERE status='pending' LIMIT 100")]


class Decision(BaseModel):
    approve: bool


@app.post('/api/instructor/submissions/{sid}')
def review(sid: str, decision: Decision, user=Depends(instructor)):
    with db() as conn:
        row = conn.execute('SELECT * FROM submissions WHERE id=?', (sid,)).fetchone()
        if not row:
            raise HTTPException(404, 'Submission not found.')
        conn.execute('UPDATE submissions SET status=? WHERE id=?', ('approved' if decision.approve else 'revise', sid))
        if decision.approve:
            conn.execute('INSERT OR IGNORE INTO grants VALUES (?,?,?)', (row['owner'], row['fingerprint'], row['topic']))
        else:
            conn.execute('DELETE FROM grants WHERE owner=? AND fingerprint=? AND topic=?', (row['owner'], row['fingerprint'], row['topic']))
    return {'ok': True}


dist = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if dist.exists():
    app.mount('/assets', StaticFiles(directory=dist/'assets'), name='assets')


@app.get('/')
def index():
    if not (dist/'index.html').exists():
        raise HTTPException(503, 'Build frontend with npm run build, or use Vite on port 5173.')
    return FileResponse(dist/'index.html')
