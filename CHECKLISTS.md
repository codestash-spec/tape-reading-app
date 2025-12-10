# CHECKLISTS.md — Checklists Operacionais e Institucionais

## C.1 – Preparação da Sessão (Pré-Mercado)
- Verificar conectividade (rede, VPN, gateway IBKR/TWS).
- Validar perfil (`PROFILE`) e configurações (host/port/client_id, símbolos).
- Confirmar permissões de market data e trading (paper/prod).
- Revisar calendário de eventos e volatilidade esperada.
- Ativar telemetria (log level adequado) e coletores.
- Carregar limites de risco (tamanho, exposição, throttle, kill-switch teste).

## C.2 – Microestrutura (Durante Sessão)
- Monitorar latência de feed; detectar staleness.
- Observar DOM para liquidez e gaps; identificar spoofing/absorção.
- Acompanhar Delta/CVD e Speed of Tape para regime de fluxo.
- Validar correção de normalização (ticks/trades/DOM) versus referência.

## C.3 – Execução (Antes de enviar ordem)
- Verificar símbolo e mapa futuro→CFD (se aplicável).
- Checar preço de referência e collar (se configurado).
- Confirmar limites por ordem (size, notional) e exposição residual.
- Validar rota/adaptador (sim vs IBKR/MT5) e ambiente (paper vs prod).
- Kill-switch em modo seguro (testado) e pronto para uso.

## C.4 – Checklist Diário do Risk Officer
- Checar PnL acumulado vs. limites diários.
- Avaliar exposição por símbolo e por broker.
- Contar rejeições de risco (motivos) e eventos de throttle.
- Verificar health de feed/execução; incidentes e latência.
- Revisar logs/audit de ordens e decisões de risco.

## C.5 – Deploy Institucional (Nova Versão)
- Build validado; testes (unit/integration/replay) verdes.
- Changelog e notas de versão; aprovação de revisão.
- Rollback plan documentado; configuração versionada.
- Kill-switch e cancel-all verificados em ambiente de staging/paper.
- Observabilidade habilitada; alarmes de saúde prontos.

## C.6 – Segurança e Governança
- Segredos fora do VCS; armazenados em secret store/envs seguros.
- Permissões de acesso por papéis (dev/ops/audit).
- Auditoria habilitada para risco/execução; logs imutáveis.
- Revisão de dependências e licenças; updates de segurança aplicados.

## C.7 – Replay Engine
- Dataset validado (timestamps ordenados, schema correto).
- Configuração de pacing (`speed`) e modo determinístico.
- Sincronização de DOM/Delta/Tape durante replay.
- Métricas/logs de replay habilitados para diagnóstico.

## C.8 – Treino de Modelos ML (se aplicável)
- Dataset com labels/verificação; splits (train/val/test) definidos.
- Features documentadas; thresholds operacionais mapeados.
- Avaliação offline e thresholds antes de ativar em produção.
- Rollback e flags de feature/ML para desligar rapidamente.

## C.9 – Final de Sessão
- Fechar posições abertas; cancelar ordens pendentes.
- Exportar/auditar logs e decisões de risco/execução.
- Gerar relatório de latência, incidentes e rejeições.
- Desativar credenciais/gateways conforme política.
