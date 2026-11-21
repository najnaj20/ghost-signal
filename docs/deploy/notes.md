# Deploy notes

## Live on the VPS (22 Nov 2026)

- Dashboard: http://43.156.56.188:8501/
- API (read-only): http://43.156.56.188:8501/api/feed , docs at http://43.156.56.188:8501/api/docs

Plain HTTP only. HTTPS needs a domain pointed at 43.156.56.188.

Layout:
- Caddy (system service, `deploy/Caddyfile` copied to `/etc/caddy/Caddyfile`) listens on :8501.
  `/api/*` goes to uvicorn on 127.0.0.1:8000 with the prefix stripped. Everything else goes to Streamlit on 127.0.0.1:8502.
  Non-GET requests to `/api/*` get 405, so strangers cannot edit the watchlist through the API.
- `deploy/ghost-api.service` and `deploy/ghost-dashboard.service` are systemd user units
  (copied to `~/.config/systemd/user/`, enabled, linger on), so both start on boot and restart on failure.

Why port 8501 and not 80: on this VPS, ports 80 and 443 are DNAT'd by k3s (Traefik svclb) to a pod,
so traffic never reaches Caddy there. Port 8501 was already open in ufw and the Tencent Cloud firewall.
For port 80 you would either remove the k3s Traefik LoadBalancer or add a Traefik route to 127.0.0.1:8501.

Known limit: the watchlist buttons in the dashboard still write to the shared DB (the dashboard calls
Python functions directly, not the API). Any visitor can change the watchlist. Fine for a demo.

Install / reinstall:

    cp deploy/ghost-*.service ~/.config/systemd/user/ && systemctl --user daemon-reload
    systemctl --user enable --now ghost-api ghost-dashboard
    sudo cp deploy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy

## Vercel: no

Vercel runs serverless functions. Streamlit needs a long-running process and a websocket
(`/_stcore/stream`), so the dashboard cannot run there. The FastAPI app could run as a function
only with rework (an ASGI adapter, and SQLite would be read-only and reset on each deploy).
Not worth it while the VPS works.

## Streamlit Community Cloud: possible, one blocker

Fine: `requirements.txt` covers every third-party import (networkx, fastapi, uvicorn, streamlit, pandas).
Entrypoint `src/dashboard/app.py`. Python 3.11 is what the VPS uses.

Blocker: `data/` is in `.gitignore`, so a fresh clone has no DB. `src/db.py` then creates an empty one and
the dashboard crashes on load (`IndexError` at `items[0]` in `src/dashboard/app.py`), checked with a fresh
clone on 22 Nov. Two ways out, both need Naj's decision:
1. Commit a snapshot DB (1.6 MB): `git add -f data/ghost-signal.db`. Data then goes stale unless re-committed.
2. Fix the empty-DB crash (a code change, blocked by the feature freeze) and accept an empty demo.

Clicks, after the blocker is solved:
1. Open https://share.streamlit.io and sign in with GitHub (account najnaj20).
2. Click "Create app", then "Deploy a public app from GitHub".
3. Repository `najnaj20/ghost-signal`, branch `main`, main file path `src/dashboard/app.py`.
4. Advanced settings: Python 3.11. No secrets needed.
5. Click "Deploy" and wait for the build log to finish.
