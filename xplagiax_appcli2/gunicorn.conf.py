"""
gunicorn.conf.py — Production server config.

WEB_CONCURRENCY / GUNICORN_THREADS wiring: the previous Dockerfile CMD passed
gunicorn flags as a JSON exec-array, which Docker never expands env vars in —
`ENV WEB_CONCURRENCY=3` was declared but nothing ever read it, so gunicorn
silently ran its own built-in default of 1 worker regardless of what was set
via `-e` at `docker run`. A single sync worker serializes every request in the
app (every user, every route, every background poll) through one process at a
time — and this screen's own analysis flow fires 3 concurrent requests per
click (AI/FinderX/Citations via Promise.allSettled) where the AI leg can block
for up to 90s waiting on xota. That's enough on its own to exhaust a 1-worker
pool and drop unrelated concurrent requests with a connection-level failure
(no HTTP status at all) rather than a clean error.

worker_class=gthread (not sync): these requests are I/O-bound (waiting on
xota/FinderX HTTP calls, GIL released during socket waits), so threads add
real concurrency per worker without the RAM/CPU cost of more OS processes —
same reasoning xota's own gunicorn.conf.py already applies.
"""
import os

bind = "0.0.0.0:5003"
worker_class = "gthread"
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))
threads = int(os.environ.get("GUNICORN_THREADS", "8"))

# Mata cualquier worker colgado (auto-recuperación).
timeout = 120
# Drenaje limpio al reiniciar/parar.
graceful_timeout = 30
# Recicla workers periódicamente (evita fugas/estados zombis).
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
