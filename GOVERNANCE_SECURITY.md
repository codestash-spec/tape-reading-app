# GOVERNANCE_SECURITY.md — Governança e Segurança

## Gestão de Segredos
- Não versionar segredos reais; usar env vars ou secret stores.
- Criptografia em repouso e em trânsito; controle de acesso a perfis produtivos.
- `secrets.example.yaml` é apenas modelo.

## Separação de Papéis
- **Desenvolvedor**: sim/replay, sem credenciais reais; leitura de logs de dev.
- **Operador**: roda paper/prod, aciona kill-switch, monitora métricas.
- **Auditor**: leitura de logs/audit; sem permissão de envio de ordens.

## Governança de Releases
- Semver por fase (v0.3.x Fase III).
- PRs com revisão dupla para alterações em risco/exec.
- Changelog obrigatório, tags assinadas, configs versionadas.
- Aprovação operacional para mudanças em perfis produtivos.

## Incidentes e Kill-switch
- Acionar kill-switch ao detectar comportamento anômalo; cancelar ordens ativas.
- Registrar incidente em audit log; comunicar operador/auditor.
- Retomar somente após checagem de exposição, saúde do feed e limites.
