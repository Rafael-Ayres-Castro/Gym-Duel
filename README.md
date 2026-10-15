# Gym Duel

Web app mobile-first para um casal competir na academia. Cada check-in vira pontos, e o placar semanal compara **a % da meta pessoal** de cada um, para que níveis diferentes de treino tenham a mesma chance de ganhar.

Este é o **MVP**: login e cadastro, home/placar, check-in com tela de sucesso, histórico e uma tela de regras que explica a pontuação, no celular e no computador. O documento de requisitos completo está em [docs/requisitos.md](docs/requisitos.md), e o design de referência (Claude Design) está em [design/](design/).

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

# 5. (Opcional) Dados de demonstração: Rafael e Ana com 16 treinos
python scripts/seed_demo.py

# 6. Servidor
uvicorn app.main:create_app --factory --app-dir backend --reload
```

Depois, abra **http://localhost:8000** no navegador do Windows. O WSL2 repassa o `localhost` automaticamente. A documentação interativa da API fica em **http://localhost:8000/docs**.

**Login de demonstração** (depois do passo 5): `rafael@email.com` ou `ana@email.com`, senha `gymduel`.

O seed se recusa a rodar se já houver usuários. Use `python scripts/seed_demo.py --reset` para **apagar tudo** e recriar a demonstração. As datas dos treinos são relativas à semana atual, e treinos que cairiam depois de hoje são pulados.

### Testar no celular, na mesma rede Wi-Fi

O jeito mais simples é ativar o modo de rede espelhado do WSL. Crie `%UserProfile%\.wslconfig` com `[wsl2]` e `networkingMode=mirrored`, rode `wsl --shutdown` e abra o WSL de novo. Depois:

1. Suba o servidor com `--host 0.0.0.0`.
2. No celular, abra `http://<IP-do-Windows>:8000`.
3. Se não abrir, libere a porta 8000 no Firewall do Windows.

## Testes

```bash
pytest
```

Os testes cobrem a fórmula de pontos, a % da meta, o desempate do líder, a sequência, a virada de semana, as regras de check-in (só hoje ou ontem, 1 por dia), o limite de 2 cadastros, as permissões e as mensagens do placar. Cada teste usa um banco SQLite próprio e um relógio controlável.

### Screenshots para comparar com o design

```bash
playwright install chromium   # na primeira vez
python scripts/screenshots.py
```

O script sobe um servidor temporário com banco descartável, então seus dados não são tocados. Ele gera as telas em `screenshots/`: mobile 390×844 e desktop 1440×900. Se o Chromium reclamar de bibliotecas faltando, rode `sudo .venv/bin/playwright install-deps chromium`.

## Estrutura

```
backend/
  app/
    main.py          cria o app: API em /api + frontend estático em /
    config.py        configurações lidas de variáveis de ambiente / .env
    clock.py         "hoje" em America/Sao_Paulo (injetável nos testes)
    db.py, models.py banco e tabelas: users, workouts, weekly_goals
    schemas.py       formatos de entrada e saída da API
    security.py      bcrypt, JWT e o usuário logado
    scoring.py       REGRAS PURAS: pontos, semana, %, líder, sequência, mensagens
    services/        consultas ao banco que alimentam as regras (placar, check-in...)
    routers/         rotas HTTP finas: auth, me, workouts, scoreboard, rules
  tests/             pytest
frontend/
  index.html
  css/               tokens do design → base → componentes → layout → telas
  js/
    core/            fetch da API, sessão, roteador por hash, eventos, template seguro
    domain/          regras de exibição: fórmula da prévia, rótulos de data, textos
    ui/              componentes: avatar, linha de treino, toast, confete
    layout/          casca do app: barra inferior (mobile) e menu lateral (desktop)
    screens/         login, cadastro, home, histórico, regras
    checkin/         check-in em tela cheia/modal e tela de sucesso
scripts/
  seed_demo.py       dados de demonstração
  screenshots.py     screenshots das telas
design/              arquivos do Claude Design (referência visual)
```

A regra de negócio vive em funções puras (`backend/app/scoring.py`). Os serviços buscam os dados e chamam essas funções, e as rotas só validam a entrada e devolvem a resposta. O frontend repete a fórmula de pontos apenas para a prévia do check-in. O valor que vale é sempre o calculado e gravado pelo backend.

## Regras do MVP

| Regra | Como funciona |
| --- | --- |
| Pontos por treino | `max(5, round(minutos / 3) + ajuste)`, com Leve −5, Moderada 0 e Alta +5. Ex.: 30 min moderada = 10; 45 min alta = 20 |
| Semana | De segunda a domingo, no fuso de São Paulo |
| % da meta | `min(100, round(treinos da semana / meta × 100))`. É a % que decide o placar |
| Líder | Maior %. No empate, mais pontos. Se ninguém treinou ou houver empate total, não há líder |
| Sequência | Semanas encerradas seguidas com a meta batida, +1 se a semana atual já bateu |
| Meta | Guardada por semana (`weekly_goals`). Mudar a meta vale da semana atual em diante, sem reescrever o passado |
| Check-in | Só para hoje ou ontem, 1 treino pontuado por dia (`MAX_WORKOUTS_PER_DAY`). Duração de 5 a 300 min, observação de até 140 caracteres |
| Cadastro | Fecha quando existem 2 usuários (`MAX_USERS`). O oponente de cada um é o outro |
| Cores | O primeiro cadastrado é azul e o segundo é rosa, sempre (cada pessoa mantém a sua cor) |

## API

Todas as rotas ficam em `/api` e exigem `Authorization: Bearer <token>`, exceto cadastro, login e health. Os detalhes de cada resposta estão em `/docs`.

| Método | Rota | O que faz |
| --- | --- | --- |
| POST | `/auth/register` | Cria a conta (nome, e-mail, senha, meta 1–7) e devolve o token |
| POST | `/auth/login` | Entra e devolve o token |
| GET / PATCH | `/me` | Lê ou atualiza nome e meta semanal |
| POST | `/workouts` | Registra o treino e devolve o treino, o placar novo e a mensagem da tela de sucesso |
| GET | `/workouts` | Lista treinos, com filtros `person=all\|me\|opponent`, `period=week\|month\|all` e `limit` |
| DELETE | `/workouts/{id}` | Apaga um treino próprio (os pontos vão junto) |
| GET | `/scoreboard` | Placar da semana: %, pontos, sequência, líder, mensagem e dias treinados |
| GET | `/summary` | Totais de cada um no período, usados no topo do histórico |
| GET | `/rules` | Regras em vigor (fórmula, limites, check-ins por dia) e exemplos calculados, usados na tela Regras |
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
| `APP_TODAY` | (vazio) | **Só desenvolvimento:** finge que hoje é `AAAA-MM-DD`. Nunca use em produção |

## Publicar no Render

1. Suba o repositório para o GitHub (o `.env` fica fora pelo `.gitignore`).
2. No Render, escolha **New → Blueprint** e selecione o repositório. O arquivo [render.yaml](render.yaml) já define o serviço web, os comandos, o health check e gera um `JWT_SECRET` aleatório.
3. **Banco de dados:** no plano gratuito do Render, o disco do serviço web é temporário. Um SQLite ali **perde os dados a cada deploy ou reinício**. Para uso de verdade, crie um PostgreSQL e cole a URL em `DATABASE_URL`, no painel do serviço. A URL pode vir do Postgres do próprio Render ou de um provedor com plano gratuito, como Neon ou Supabase. O app aceita `postgres://...` e cria as tabelas sozinho na primeira vez.
4. Abra a URL `https://<seu-servico>.onrender.com`, criem as duas contas e pronto: o cadastro fecha sozinho depois da segunda.

Se preferir configurar à mão (**New → Web Service**), use:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:create_app --factory --app-dir backend --host 0.0.0.0 --port $PORT`
- Variáveis: `JWT_SECRET` (gerada com `openssl rand -hex 32`) e `DATABASE_URL`.

Os planos gratuitos mudam com frequência. Confira os limites atuais: o serviço gratuito do Render "dorme" depois de um tempo sem uso, e o primeiro acesso seguinte demora alguns segundos.

## Fora do MVP (próximas fases)

Loja de prêmios, desafios, metas com bônus, badges, foto do treino, gráficos, feed, notificações e PWA. Na interface, Prêmios e Perfil aparecem como **EM BREVE**. A API já permite trocar a meta (`PATCH /me`) e apagar treinos (`DELETE /workouts/{id}`), mas essas ações ainda não têm tela.
