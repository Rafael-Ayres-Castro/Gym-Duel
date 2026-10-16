# Gym Duel: estado atual do projeto

Atualizado em 16/10/2026. Atualize este arquivo ao fim de cada etapa grande (é importado pelo CLAUDE.md).

## Resumo

Web app mobile-first em que Rafael e a namorada competem na academia: cada treino vira pontos, o placar semanal compara a **% da meta pessoal** e os pontos viram prêmios reais. **MVP e fase 2 estão implementados, testados e commitados.** Falta publicar (deploy) e as fases futuras.

- **Fase 1 (MVP):** login/cadastro, home com placar, check-in, histórico.
- **Fase 2:** regras de pontos configuráveis (proposta e aprovação), metas e sequências com selos, foto como prova, loja de prêmios com resgates, desafios entre o casal.
- **Minha conta** (`#/account`, 16/10/2026, ainda sem commit): abre pelo avatar da Home (celular) ou pelo card do usuário no menu lateral (desktop). Mostra perfil, pontos (saldo, ganhos, gastos) e conquistas de todo o período (`GET /me/stats`), troca nome, e-mail (`PUT /me/email`) e senha (`PUT /me/password`), as duas últimas pedindo a senha atual, e troca rápida entre contas salvas no aparelho. Substituiu o antigo menu suspenso do avatar (`ui/account-menu.js`, removido).

Fontes de verdade: o design em `design/` (`Gym Duel Web.dc.html` é o MVP, `Gym Duel Web v2.dc.html` é a fase 2; `support.js` é só o runtime do Claude Design e **não** vai para o app) e o [README.md](../README.md), que descreve as regras e a API reais. O `docs/requisitos.md` é a visão inicial e **diverge** da pontuação real (ver Pendências).

## Como rodar e testar

```bash
source .venv/bin/activate
pytest                                   # 142 testes, ~15 s
python scripts/seed_demo.py --reset      # demo completa (Rafael/Ana, senha gymduel)
uvicorn app.main:create_app --factory --app-dir backend --reload   # http://localhost:8000 , /docs
python scripts/screenshots.py            # screenshots 390×844 e 1440×900 em screenshots/
```

- `.env` local com `JWT_SECRET` (mín. 32 caracteres). `APP_TODAY=AAAA-MM-DD` finge o "hoje" (só dev; os testes usam um relógio injetável).
- **Quirks deste ambiente (Ubuntu 26.04 / WSL):** o `.venv` foi criado sem `ensurepip` (`python3 -m venv --without-pip` + `get-pip.py`). O Chromium do Playwright não achava `libnss3/libnspr4/libasound2`; foram extraídos em `~/.cache/gymduel-chromium-libs`, então para screenshots use `LD_LIBRARY_PATH=~/.cache/gymduel-chromium-libs/root/usr/lib/x86_64-linux-gnu`. A correção definitiva é `sudo apt install python3.14-venv` e `sudo .venv/bin/playwright install-deps chromium`.
- Banco de dev: `gymduel.db` na raiz. Fotos de dev: `data/photos/`. Os dois são ignorados pelo Git.

## Arquitetura (resumo; detalhes no README)

- **Backend** `backend/app/`: FastAPI + SQLAlchemy 2. `scoring.py` tem as **regras puras** (pontos, semana, %, líder, sequência, selos, desafios). `services/` busca dados e chama as regras; `routers/` são finos. `maintenance.py` roda antes de cada requisição e fecha semanas e desafios vencidos (**não há cron**). `storage.py`: fotos locais ou S3. Migrações Alembic em `backend/migrations/` (0001 MVP, 0002 regras/sequências, 0003 prêmios, 0004 desafios), aplicadas sozinhas na subida (`AUTO_MIGRATE`; os testes usam `create_all`).
- **Frontend** `frontend/`: HTML/CSS/JS puros, módulos ES, sem build, servido pelo FastAPI. `js/core` (API, sessão, roteador por hash, eventos, template com escape), `js/domain` (textos e regras de exibição), `js/ui` (componentes), `js/layout` (casca com barra inferior/menu lateral), `js/screens/*`, `js/checkin`. CSS em camadas: tokens → base → componentes → layout → telas.
- **Testes** `backend/tests/`: um banco SQLite por teste e relógio controlável (`clock`, `Player` helpers em `conftest.py`).

## Regras e decisões que não são óbvias

- Pontos: `max(5, round(min / min_por_ponto) ± intensidade + bônus_foto)`. O backend grava `points` no treino; o frontend só repete a fórmula para a prévia.
- A semana (seg a dom, fuso São Paulo) **fecha na terça** (domingo ainda aceita check-in como "ontem"). Fechar é preguiçoso e idempotente. Apagar treino só vale para hoje/ontem, para semanas fechadas nunca mudarem.
- Mudar a **meta** vale da próxima semana. Mudar **regras de pontos** exige proposta aprovada pelo outro; ao aprovar recalcula só a semana em curso.
- Saldo = pontos dos treinos + `point_ledger` (selos, vencedor da semana, desafios, resgates negativos). Resgatar não mexe no placar.
- Desafios: empate não tem vencedor; "primeiro a bater a meta" desempata por data do treino e depois horário do check-in; só quem recebeu aceita/recusa; só o autor cancela.
- O app é para 2 pessoas (`MAX_USERS=2`); primeiro cadastrado = azul, segundo = rosa; "oponente" = o outro.
- Sem `couple_id`: a instalação inteira é o casal.
- Custos de prêmio permitidos: 50, 100, 150, 200, 300. Os valores do protótipo (60/120/180) foram ajustados no seed.
- Conta: senha errada ao confirmar troca de e-mail/senha devolve **403** `wrong_password` (não 401, que o frontend trata como sessão expirada e desloga). Trocar a senha **não** invalida tokens de outros aparelhos (JWT sem estado; exigiria uma coluna de versão do token).
- Contas salvas no aparelho: `localStorage` `gymduel.accounts` guarda `{id, firstName, email, color, token}` de cada conta que entrou. "Trocar de conta" troca o token ativo sem senha; "Entrar com outra conta" (`session.park`) mantém a atual salva; "Sair" (`session.clear`) remove a atual da lista. Token vencido ao trocar cai no fluxo normal de sessão expirada.
- Helpers de formulário (`fieldError`, `setFieldError`, `withBusyButton`, `EMAIL_PATTERN`, olho da senha) ficam em `frontend/js/ui/form.js`, e `sheetHead` em `ui/sheet.js`: compartilhados por login, cadastro, prêmios e conta.

## Convenções

- Código, comentários e commits em **inglês**; interface e documentação em **português do Brasil**.
- Um commit por etapa. Rodar `pytest` antes de commitar. Comparar telas com o design por screenshots (mobile 390 e desktop 1440).
- Armadilhas já resolvidas: `form.name` num `<form>` é o atributo do próprio form (use `form.elements.namedItem('name')`); o atributo `hidden` precisa vencer `display:*` (regra global em `base.css`); `Math.round` vs `round()` (o backend usa `_round_half_up`).
- Scripts de apoio dos screenshots interativos viviam no scratchpad temporário e **não** foram versionados. O que persiste é `scripts/screenshots.py`.

## Pendências e próximos passos

1. **Publicar** no Render (`render.yaml` pronto). Para fotos em produção é preciso criar um bucket **privado** (Cloudflare R2 ou Supabase Storage) e definir `PHOTO_STORAGE=s3` e `S3_*`. O envio para S3 só foi testado com cliente simulado. Para o banco, usar PostgreSQL em `DATABASE_URL` (as migrações não foram rodadas contra Postgres ainda).
2. **Sincronizar `docs/requisitos.md`** com as regras reais de pontuação (o README já está certo): a fórmula, o desempate, as sequências, os prêmios e os desafios mudaram em relação ao documento inicial.
3. Revisar as regras com a namorada depois de 2 a 3 semanas de uso.
4. Falta: recuperação de senha, foto de perfil, desconectar outros aparelhos ao trocar a senha, editar/remover prêmios, trocar o nome do app (é provisório).
5. Fases futuras: badges gerais, gráficos de evolução, feed com reações, notificações push e PWA instalável.
