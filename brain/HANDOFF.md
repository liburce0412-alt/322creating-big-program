# HANDOFF - CampusAI

## Current State
- Website http://campus3ai.xyz/ homepage returns 200
- Flask API returns 502 (c_bridge.py type hint issue)
- Git repo merged and pushed
- brain/ dir created but files not fully written

## Next Steps
1. Fix c_bridge.py: dict | list -> dict (Python 3.6)
2. Restart Flask: nohup gunicorn ... --daemon
3. Verify API endpoints
4. Add .gitignore, commit and push brain/

## Unwritten Thoughts
- VNC can restart services too
- Nginx proxy_pass trailing slash issue for /api/ routes
