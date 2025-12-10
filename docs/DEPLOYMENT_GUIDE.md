# Deployment Guide

## Ambientes
- dev: simulação local, observabilidade básica
- paper: sim + telemetria ampliada
- prod: IBKR live, observabilidade completa

## Perfis
- Config em `config/profiles/{dev,paper,prod}.yaml`
- Seleção via env `PROFILE`

## Pipeline
1. Lint/Test
2. Build pacote
3. Deploy (dev/paper/prod)
4. Health check e watchdog

## Rollback
- `deployment.rollback.rollback_plan(<versao>)`
- Reverter artefato e validar health

## Secrets
- Fora do Git, referência por env; exemplo `config/secrets.example.yaml`

## CI/CD
- Declarado em `deployment.cicd.CICDWorkflow`
- GitHub Actions: lint → test → package → deploy
