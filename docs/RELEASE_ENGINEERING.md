# Release Engineering

## Versionamento
- Série 0.4.x para Fases IV–VII
- Tagging semver: v0.4.0, v0.4.1...

## Branching
- main protegido
- feature branches para engines/estratégia/execução/observabilidade

## Pipeline de Release
1. Merge feature → main
2. CI executa lint/test
3. Build e publicação de artefato
4. Tag git e changelog

## Artefatos
- Pacote Python (wheel)
- Imagem container (opcional)
- Documentação em `docs/`

## Governança
- Aprovação obrigatória
- Auditoria via logs JSON e git tags
