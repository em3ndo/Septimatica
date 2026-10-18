# Septimatica

A graph-theory learning notebook for HMC Math 55: React + FastAPI + NetworkX,
with Gemini tutoring and optional local Lean certificate verification.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
.venv/bin/uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Configuration is read from the repository `.env`.
Use `.env.example` as a reference; never commit real keys. For frontend development,
run `npm run dev` in `frontend` and open port 5173. Vite proxies `/api` to port 8000.

`ALLOW_DEMO_LOGIN=true` enables local practice sessions only when `APP_ENV` is not
`production`. These sessions are explicitly not HMC accounts and open analysis tools
for exploration. SQLite saves their graphs until deleted, but a new demo login creates
a new identity. School accounts retain notebooks across logins.

## What is implemented

- Pan/zoom graph workspace: Shift-drag, middle-drag, or Pan mode; scroll to zoom
  about the pointer; zoom buttons, keyboard arrow panning, Fit graph, Reset view.
  Coordinates are not limited to the visible canvas. Numerical limits are ±10¹²;
  computational limits remain 80 vertices / 500 edges.
- Add, connect, move and erase vertices/edges, undo/redo, example graphs, layouts,
  adjacency lists/matrices, JSON import/export, and private saved notebooks.
- Planarity via NetworkX's LR algorithm, bipartiteness, components/trees, Euler walks,
  and DSATUR coloring with bounded exact search. Exact search is limited to 24 vertices
  and 0.4 seconds; unproven optima are explicitly reported as lower/upper bounds.
- School OIDC login integration, server-side sessions, owner-scoped storage, instructor
  roles, course release dates, protected graph isomorphism checks, and proof review.
- Gemini sees the graph, recent conversation, and only already-unlocked analysis.
  It offers hints and informal reasoning feedback rather than finished proofs.
- Student witnesses: proper coloring, two-coloring, odd cycles, planar rotation
  systems, and K5/K3,3 minor branch sets. Validity is checked locally. Written proofs
  go to an instructor; AI opinions never independently unlock tools.

## External services and configuration

**Google Gemini is the only AI API used.** The server calls
`generativelanguage.googleapis.com` with `GEMINI_API_KEY`; the key is never included
in frontend assets, URLs, or client responses. `GEMINI_MODEL` is configurable;
the tested model is `gemini-3.8-flash`. Students opt in before sending graph and
message content to Google. No school email or SSO token is sent to Gemini.
The supplied development key is stored only in the ignored `.env` with owner-only
permissions. Rotate any credential shared in a conversation before public deployment.

**Institutional identity provider:** HMC IT must register this application before
real school login can work. Request an OpenID Connect client with issuer URL,
client ID/secret, the `openid email profile` scopes, and a registered callback URL.
Set `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_REDIRECT_URI`.
The implementation uses discovery, authorization code with PKCE, signed ID-token
validation through Authlib, state/nonce, issuer checks and verified email domains.
Default allowed domains: `hmc.edu,g.hmc.edu`. Authentication keys users by issuer
and subject, not email. If HMC offers only SAML for this application, an IT-approved
SAML integration is still needed; do not substitute email-only or password capture.
This is the only additional external integration; there is no hosted auth vendor.

**Lean:** local open-source executable, no account or API key. Install Lean 4 from
https://lean-lang.org/install/ and set `LEAN_BIN` if needed. Only server-generated
templates containing validated integers are compiled. No student or Gemini code is
executed. Lean checks proper coloring and its stated upper bound with `by decide`;
it does not prove minimality, check arbitrary natural-language proofs, or formally
prove the NetworkX planarity algorithm. Compiler absence/timeouts are reported as
`unavailable`, never as verification. Compilation has a 12-second wall-clock limit,
1 GB Lean memory limit, and a fixed heartbeat budget.

## Course setup

The baseline is https://math.hmc.edu/su/math55/ (Spring 2026 page). It covers graph
theory alongside combinatorics and number theory, and permits supplemental AI
learning rather than solutions to assigned work. This app implements only the
graph-theory portion. No answer keys were collected or used for training.

Set `INSTRUCTOR_EMAILS` to a comma-separated list of verified instructor emails.
After SSO login, those accounts see the course-policy editor and pending proof queue.
All student topics are locked by default. Example policy:

```json
{
  "released": ["connectivity", "bipartite"],
  "release_at": {"planarity": "2027-04-10T09:00:00-07:00"},
  "protected_graphs": [],
  "require_proof": true
}
```

Available topics: `coloring`, `planarity`, `bipartite`, `connectivity`, `eulerian`.
Protected entries use the same `{nodes, edges}` schema as exported graphs. Protection
is based on isomorphism, so renaming/repositioning vertices does not evade it.
It does not recognize arbitrary reworded assignments, supergraphs, or modified graphs.
Instructors must register the actual protected graphs; none are assumed to be homework.
For a new semester, update the policy deliberately rather than relying on old dates.

Valid planarity/bipartite witnesses grant access for that student's exact labeled
topology, subject to release and protection rules. Moving vertices preserves access;
changing vertices/edges invalidates it. A proper coloring is only an upper bound,
so revealing minimum coloring still requires instructor approval. Connectivity and
Eulerian written arguments also require instructor review. An accepted certificate
does not certify every sentence in the accompanying prose.

The tutor is prompted to avoid answer-giving, and protected/self-declared assigned
work is blocked before calling Gemini. Language-model prompt compliance cannot
guarantee cheating prevention; course policy and instructor oversight are essential.

## Verification

```bash
.venv/bin/python -m pytest -q
# Optional integration tests with an installed local Lean compiler:
RUN_LEAN_TESTS=1 .venv/bin/python -m pytest -q backend/tests/test_live_lean.py
cd frontend
npm run lint
npm run build
```

Tests cover graph algorithms, density/matrix regressions, bounded coloring, empty
graphs, certificates, access control, ownership, graph-bound grants, instructor
review, release dates, protected graph relabeling, request sizes, and unbounded
canvas coordinates. Unit tests do not call Google or require Lean.

## Before institutional deployment

Complete the real HMC SSO registration and test sign-in with IT. Set
`APP_ENV=production`, a strong random `SESSION_SECRET` (32+ characters), the HTTPS
callback, a private persistent `DATABASE_PATH`, and approved instructor emails.
Demo login is forcibly disabled in production. Put the single application process
behind an HTTPS reverse proxy with request/concurrency limits and backups. The
current per-user tutor limiter is process-local; use a shared limiter before running
multiple workers. School security/privacy review and Gemini data-handling approval
remain deployment responsibilities. No public deployment was performed.
