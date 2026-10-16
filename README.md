# Gym Duel

Web app mobile-first para um casal competir na academia. Cada check-in vira pontos, e o placar semanal compara **a % da meta pessoal** de cada um, para que níveis diferentes de treino tenham a mesma chance de ganhar.

O app já tem:

- **MVP:** login e cadastro, home/placar, check-in com tela de sucesso e histórico.
- **Fase 2:**
  - regras de pontos configuráveis, aprovadas pelos dois;
  - metas semanais com sequências e selos;
  - foto como prova do treino;
  - loja de prêmios com resgates;
  - desafios entre o casal.

Tudo funciona no celular e no computador. O documento de requisitos está em [docs/requisitos.md](docs/requisitos.md), e o design de referência (Claude Design) está em [design/](design/). O protótipo da fase 2 é o `Gym Duel Web v2.dc.html`.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic. Senhas com bcrypt e login com JWT (válido por 30 dias).
- **Banco:** SQLite no desenvolvimento. Em produção, PostgreSQL via `DATABASE_URL`.
- **Frontend:** HTML, CSS e JavaScript puros (módulos ES, sem build), servidos pelo próprio FastAPI. É um único deploy, sem CORS.
- **Testes:** pytest + httpx. Screenshots com Playwright.

## Como rodar no WSL

Mantenha o projeto **no filesystem do Linux** (por exemplo `~/projetos/gym-duel`), não em `/mnt/c`. Em `/mnt/c` o acesso a arquivos fica muito lento e o `--reload` não detecta mudanças.

```bash
# 1. Python com venv (no Ubuntu, o venv vem num pacote separado)
sudo apt update && sudo apt install -y python3 python3-venv

# 2. Código
mkdir -p ~/projetos && cd ~/projetos
git clone <url-do-repositorio> gym-duel && cd gym-duel

# 3. Ambiente virtual e dependências
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 4. Configuração: copie o exemplo e gere uma chave JWT aleatória
cp .env.example .env
sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" .env

# 5. (Opcional) Dados de demonstração: Rafael e Ana com treinos, fotos, prêmios e desafios
python scripts/seed_demo.py

# 6. Servidor
uvicorn app.main:create_app --factory --app-dir backend --reload
```

Depois, abra **http://localhost:8000** no navegador do Windows. O WSL2 repassa o `localhost` automaticamente. A documentação interativa da API fica em **http://localhost:8000/docs**.

**Login de demonstração** (depois do passo 5): `rafael@email.com` ou `ana@email.com`, senha `gymduel`.

O seed se recusa a rodar se já houver usuários. Use `python scripts/seed_demo.py --reset` para **apagar tudo** e recriar a demonstração. As datas dos treinos são relativas à semana atual, e treinos que cairiam depois de hoje são pulados.

O banco é criado e atualizado sozinho na subida do servidor, pelas migrações do Alembic (`backend/migrations/`). Um banco antigo do MVP é reconhecido e atualizado sem perder dados.

### Testar no celular, na mesma rede Wi-Fi

O jeito mais simples é ativar o modo de rede espelhado do WSL. Crie `%UserProfile%\.wslconfig` com `[wsl2]` e `networkingMode=mirrored`, rode `wsl --shutdown` e abra o WSL de novo. Depois:

1. Suba o servidor com `--host 0.0.0.0`.
2. No celular, abra `http://<IP-do-Windows>:8000`.
3. Se não abrir, libere a porta 8000 no Firewall do Windows.

## Testes

```bash
pytest
```

Cada teste usa um banco SQLite próprio e um relógio controlável. Eles cobrem:

- **Pontuação e placar:** a fórmula de pontos com regras configuráveis, a % da meta, o desempate do líder, a sequência, o recorde, os selos e a virada e o fechamento de semana, com o bônus de vencedor.
- **Regras de pontos:** o ciclo proposta → aprovação → recálculo.
- **Check-in:** só hoje ou ontem, 1 por dia.
- **Foto:** limpeza do EXIF, tamanho, bônus, URL assinada, permissões.
- **Prêmios:** saldo e resgates, inclusive sem saldo.
- **Desafios:** progresso e encerramento.
- **Infraestrutura:** migrações iguais aos modelos, limite de 2 cadastros e permissões.

### Screenshots para comparar com o design

```bash
playwright install chromium   # na primeira vez
python scripts/screenshots.py
```

O script sobe um servidor temporário com banco descartável, então seus dados não são tocados. Ele gera todas as telas em `screenshots/`, inclusive Desafios, Prêmios e Metas e regras: mobile 390×844 e desktop 1440×900. Se o Chromium reclamar de bibliotecas faltando, rode `sudo .venv/bin/playwright install-deps chromium`.

## Estrutura

```
backend/
  app/
    main.py          cria o app: API em /api + frontend estático em /
    config.py        configurações lidas de variáveis de ambiente / .env
    clock.py         "hoje" em America/Sao_Paulo (injetável nos testes)
    db.py, models.py banco e tabelas
    migrate.py       aplica as migrações do Alembic na subida
    maintenance.py   antes de cada requisição: fecha semanas e encerra desafios vencidos
    schemas.py       formatos de entrada e saída da API
    security.py      bcrypt, JWT e o usuário logado
    storage.py       fotos: disco local (dev) ou bucket S3-compatível, com URLs assinadas
    scoring.py       REGRAS PURAS: pontos, semana, %, líder, sequência, selos, desafios
    texts.py         textos em pt-BR gerados no servidor (avisos)
    services/        casos de uso: placar, check-in, regras, semanas, fotos, prêmios, desafios...
    routers/         rotas HTTP finas
  migrations/        Alembic (0001 MVP, 0002 regras/sequências, 0003 prêmios, 0004 desafios)
  tests/             pytest
frontend/
  index.html
  css/               tokens do design → base → componentes → layout → telas
  js/
    core/            fetch da API, sessão, roteador por hash, eventos, template seguro
    domain/          regras de exibição: fórmula da prévia, rótulos de data, textos
    ui/              componentes: avatar, linha de treino, janela (sheet), foto, toast, confete
    layout/          casca do app: barra inferior (mobile) e menu lateral (desktop), contadores
    screens/         login, cadastro, home, histórico, desafios, prêmios, metas e regras
    checkin/         check-in em tela cheia/modal e tela de sucesso
scripts/
  seed_demo.py       dados de demonstração
  screenshots.py     screenshots das telas
design/              arquivos do Claude Design (referência visual)
```

A regra de negócio vive em funções puras (`backend/app/scoring.py`). Os serviços buscam os dados e chamam essas funções, e as rotas só validam a entrada e devolvem a resposta. O frontend repete a fórmula de pontos apenas para a prévia do check-in. O valor que vale é sempre o calculado e gravado pelo backend.

## Regras do jogo

| Regra | Como funciona |
| --- | --- |
| Pontos por treino | `max(5, round(minutos / minutos_por_ponto) ± intensidade + bônus_foto)`. Padrão: 1 ponto a cada 3 min, Leve −5, Alta +5, foto +5 |
| Regras configuráveis | Minutos por ponto (2, 3, 4), intensidade (0, 5, 10), bônus de foto (0, 3, 5, 10) e bônus do vencedor da semana (0, 10, 20, 30). Mudar exige proposta e aprovação do outro. Só o autor cancela, e quem recebe pode recusar. Ao aprovar, a semana em curso é recalculada; semanas fechadas não mudam |
| Semana | De segunda a domingo, no fuso de São Paulo |
| % da meta | `min(100, round(treinos da semana / meta × 100))`. É a % que decide o placar |
| Líder e vencedor da semana | Maior %. No empate, mais pontos. Empate total não tem líder nem bônus |
| Meta | De 1 a 7 treinos. A mudança vale **a partir da próxima semana**, para não mexer no placar em curso |
| Fechamento da semana | A semana fecha **na terça**, porque na segunda o domingo ainda aceita check-in ("ontem"). Ao fechar, ficam gravados o resultado, a sequência, os selos e o bônus do vencedor. Não há agendador: o fechamento acontece na primeira requisição depois do prazo e nunca roda duas vezes |
| Sequência e selos | Semanas seguidas com a meta batida (+1 quando a semana atual bate). Os selos de 2, 4, 8 e 12 semanas dão +10, +20, +40 e +60 pts, uma vez cada. Semana perdida zera a sequência, mas não tira pontos |
| Saldo | Pontos dos treinos + bônus (selos, vencedor da semana, desafios) − resgates. É separado do placar: resgatar não mexe na semana |
| Foto | Opcional, até 8 MB. O app reduz para 1600 px, e o servidor remove os metadados (inclusive a localização). Fica guardada em armazenamento privado, com links que valem 10 min. Se o envio falhar, o treino fica salvo sem o bônus e dá para tentar de novo |
| Prêmios | Cada um cria prêmios (50 a 300 pts) que **o outro** resgata. Ciclo: pendente → cumprido (pelo dono) → recebido (por quem resgatou). O resgate nunca deixa o saldo negativo |
| Desafios | Mais treinos ou mais minutos (por tipo, opcional), na semana ou no fim de semana, ou "primeiro a bater a meta" (só na semana). Valem +10/+20/+50 pts ou um combinado em texto. O progresso vem sempre dos treinos. Ao fim do período, maior valor vence, e **empate não tem vencedor**. "Primeiro a bater a meta" compara a data do treino e, no mesmo dia, o horário do check-in. Desafio não aceito até o fim do período some |
| Check-in | Só para hoje ou ontem, 1 treino pontuado por dia (`MAX_WORKOUTS_PER_DAY`). Apagar também só vale para hoje ou ontem, para semanas fechadas nunca mudarem |
| Cadastro | Fecha quando existem 2 usuários (`MAX_USERS`). O oponente de cada um é o outro |
| Cores | O primeiro cadastrado é azul e o segundo é rosa, sempre |

## API

Todas as rotas ficam em `/api` e exigem `Authorization: Bearer <token>`, exceto cadastro, login e health. Os detalhes de cada resposta estão em `/docs`.

| Método | Rota | O que faz |
| --- | --- | --- |
| POST | `/auth/register` | Cria a conta (nome, e-mail, senha, meta 1–7) e devolve o token |
| POST | `/auth/login` | Entra e devolve o token |
| GET / PATCH | `/me` | Lê o usuário (meta atual, próxima meta, saldo) ou atualiza nome e meta (vale na próxima semana) |
| POST | `/workouts` | Registra o treino e devolve o treino, o placar novo e a mensagem da tela de sucesso |
| GET | `/workouts` | Lista treinos, com filtros `person=all\|me\|opponent`, `period=week\|month\|all` e `limit` |
| DELETE | `/workouts/{id}` | Apaga um treino próprio de hoje ou ontem (os pontos e a foto vão junto) |
| POST | `/workouts/{id}/photo` | Envia a foto de prova (multipart) e aplica o bônus |
| POST | `/workouts/{id}/cheer` | Manda parabéns por um treino da dupla |
| GET | `/scoreboard` | Placar da semana: %, pontos, sequência, líder, mensagem e dias treinados |
| GET | `/summary` | Totais de cada um no período, usados no topo do histórico |
| GET | `/rules` | Regras em vigor, opções permitidas e proposta pendente |
| POST | `/rules/proposals` | Propõe novas regras |
| POST | `/rules/proposals/{id}/approve` e `/reject` | Aprova (recalcula a semana) ou recusa a proposta da dupla |
| DELETE | `/rules/proposals/{id}` | Cancela a própria proposta |
| GET | `/streaks` | Sequência, recorde, últimas 9 semanas e selos de cada um |
| GET / POST | `/rewards` | Saldos e loja / cria prêmio |
| POST | `/rewards/{id}/redeem` | Resgata (409 sem saldo) |
| GET | `/redemptions?scope=mine\|to_fulfill` | Meus resgates / para cumprir |
| POST | `/redemptions/{id}/fulfill`, `/receive` e `/remind` | Cumprido, recebi e lembrar |
| GET / POST | `/challenges` | Desafios (recebidos, enviados, ativos com progresso, concluídos) / cria |
| POST | `/challenges/{id}/accept` e `/decline` | Aceita ou recusa |
| DELETE | `/challenges/{id}` | Cancela um desafio enviado e ainda não aceito |
| GET | `/badges` | Contadores da navegação (desafios recebidos, prêmios a cumprir) |
| GET | `/notifications` e POST `/notifications/read` | Avisos não lidos (viram toasts) e marcar como lidos |
| GET | `/health` | Verificação de saúde (usada pelo Render) |

Os erros seguem sempre o formato `{"detail": {"code": "...", "message": "..."}}`, com a mensagem pronta em português.

## Variáveis de ambiente

| Variável | Padrão | Para quê |
| --- | --- | --- |
| `JWT_SECRET` | (obrigatória) | Assina os tokens. Mínimo de 32 caracteres: `openssl rand -hex 32` |
| `DATABASE_URL` | SQLite `gymduel.db` | URL do banco. Aceita `postgres://...` |
| `MAX_USERS` | `2` | Limite de cadastros |
| `MAX_WORKOUTS_PER_DAY` | `1` | Treinos pontuados por dia, por pessoa |
| `JWT_EXPIRE_DAYS` | `30` | Duração do login |
| `PHOTO_STORAGE` | `local` | `local` (disco em `data/photos`, para desenvolvimento) ou `s3` |
| `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | (vazio) | Bucket **privado** S3-compatível (AWS S3, Cloudflare R2, Supabase Storage) quando `PHOTO_STORAGE=s3` |
| `PHOTO_URL_TTL_SECONDS` | `600` | Validade dos links assinados das fotos |
| `AUTO_MIGRATE` | `true` | Aplica as migrações ao subir (os testes desligam) |
| `APP_TODAY` | (vazio) | **Só desenvolvimento:** finge que hoje é `AAAA-MM-DD`. Nunca use em produção |

## Publicar no Render

1. Suba o repositório para o GitHub (o `.env` fica fora pelo `.gitignore`).
2. No Render, escolha **New → Blueprint** e selecione o repositório. O arquivo [render.yaml](render.yaml) já define o serviço web, os comandos, o health check e gera um `JWT_SECRET` aleatório.
3. **Banco de dados:** no plano gratuito do Render, o disco do serviço web é temporário. Um SQLite ali **perde os dados a cada deploy ou reinício**. Para uso de verdade, crie um PostgreSQL e cole a URL em `DATABASE_URL`, no painel do serviço. A URL pode vir do Postgres do próprio Render ou de um provedor com plano gratuito, como Neon ou Supabase. O app aceita `postgres://...` e cria as tabelas sozinho na primeira vez.
4. **Fotos:** o disco do plano gratuito também é apagado. Crie um bucket **privado**, por exemplo no Cloudflare R2 ou no Supabase Storage. Depois defina no painel `PHOTO_STORAGE=s3` e as variáveis `S3_*` (bucket, endpoint e chaves de acesso). As fotos nunca ficam públicas: o app gera links assinados que expiram em 10 minutos.
5. Abra a URL `https://<seu-servico>.onrender.com`, criem as duas contas e pronto: o cadastro fecha sozinho depois da segunda.

Se preferir configurar à mão (**New → Web Service**), use:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:create_app --factory --app-dir backend --host 0.0.0.0 --port $PORT`
- Variáveis: `JWT_SECRET` (gerada com `openssl rand -hex 32`), `DATABASE_URL` e as de foto (`PHOTO_STORAGE=s3` e `S3_*`).

As migrações rodam sozinhas a cada subida. Não há agendador para configurar: semanas e desafios são fechados na primeira requisição depois do prazo.

Os planos gratuitos mudam com frequência. Confira os limites atuais: o serviço gratuito do Render "dorme" depois de um tempo sem uso, e o primeiro acesso seguinte demora alguns segundos.

## Ainda fora (próximas fases)

Badges gerais (primeiro treino, 10 treinos...), gráficos de evolução, feed com reações e comentários, lembretes e notificações push, e PWA instalável. Os avisos atuais aparecem como toasts quando o app é aberto. O app também ainda não tem recuperação de senha nem tela de perfil.
