# Deployment Configuration

This project is currently deployed with Coolify.

## Current production deployment

- Production release flow is documented in `README.md` under "Production Deployment (Coolify)".
- Deploys are triggered from GitHub Actions after CI passes.
- Coolify pulls and runs `ghcr.io/bluestemso/taylor_learns`.

## About files in this folder

- `deploy.yml` is a legacy Kamal config kept for historical reference.
- It is not the active production deployment path for this project.
