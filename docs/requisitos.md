# Gym Duel — Requisitos do Projeto

Oct 14, 2026 · @Rafael

## Visão geral

Um web app (PWA) para Rafael e a namorada competirem na academia: cada treino vira pontos, os pontos geram um ranking, e o ranking vira prêmios reais combinados entre os dois.

- **Objetivo principal:** criar constância de treino para os dois, com motivação extra para ela.
- **Público:** 2 usuários fixos (o casal), com possibilidade de convidar amigos no futuro.
- **Princípio de design:** a competição precisa ser justa (pontuação por esforço relativo, não por carga absoluta) e divertida, nunca punitiva.
- **Nome provisório:** Gym Duel (troque à vontade).

## Stack de tecnologias

Backend em Python (FastAPI) servindo uma API REST, frontend em HTML/CSS/JavaScript puro consumindo essa API via `fetch()`.

| Camada | Tecnologia | Por quê | Alternativa |
| --- | --- | --- | --- |
| Backend | Python + FastAPI | Rápido, moderno, docs automáticas em /docs | Flask |
| ORM | SQLAlchemy (ou SQLModel) | Troca de banco sem reescrever código | — |
| Banco de dados | SQLite | Zero configuração, ideal para 2 usuários | PostgreSQL ao publicar |
| Autenticação | JWT + senha com hash (passlib/bcrypt) | Login simples e seguro | Sessão com cookie |
| Upload de fotos | Pasta local no início | Simples para o MVP | Cloudinary ou S3 |
| Frontend | HTML + CSS + JavaScript puro | O que você já domina | Alpine.js ou React se crescer |
| Estilo | CSS puro ou Tailwind CSS | Tailwind acelera o layout | — |
| Gráficos | Chart.js | Leve e fácil de usar | — |
| App no celular | PWA (manifest + service worker) | Instala na tela inicial, funciona como app | — |
| Notificações | Web Push | Lembretes e provocações | E-mail ou Telegram bot |
| Hospedagem | Render ou Railway | Plano gratuito/barato, deploy via GitHub | Fly.io |
| Versionamento | Git + GitHub | Histórico e deploy automático | — |
| Testes | pytest | Testar regras de pontuação | — |

O JavaScript fica com três responsabilidades: chamar a API, atualizar a tela sem recarregar e desenhar os gráficos.

## Funcionalidades

O MVP cobre login, check-in, pontos e placar; o resto entra em fases seguintes.

| Módulo | Funcionalidade | Fase |
| --- | --- | --- |
| Conta | Cadastro e login com e-mail e senha | MVP |
| Conta | Perfil: nome, foto, meta semanal de treinos | MVP |
| Treinos | Check-in de treino: data, tipo (musculação, corrida, aula...), duração, intensidade | MVP |
| Treinos | Histórico de treinos com filtro por semana/mês | MVP |
| Treinos | Foto como prova do treino | v2 |
| Treinos | Registro de exercícios e cargas (recordes pessoais) | v3 |
| Pontos | Cálculo automático de pontos por treino | MVP |
| Pontos | Streak de dias/semanas seguidas com bônus | v2 |
| Ranking | Placar semanal e mensal (você vs. ela) | MVP |
| Ranking | Histórico de vitórias por semana | v2 |
| Metas | Meta semanal individual (ex.: 4 treinos) com bônus ao bater | v2 |
| Desafios | Desafios criados por um para o outro (ex.: 3 treinos até domingo) | v2 |
| Prêmios | Loja de prêmios cadastrados pelo casal, com custo em pontos | v2 |
| Prêmios | Resgate de prêmio e confirmação de entrega pelo outro | v2 |
| Prêmios | Prêmio do vencedor da semana/mês | v2 |
| Conquistas | Badges (primeiro treino, 10 treinos, 4 semanas seguidas...) | v3 |
| Gráficos | Evolução de pontos e treinos por semana (Chart.js) | v3 |
| Social | Feed de atividades com reações e comentários | v3 |
| Notificações | Lembrete de treino e aviso quando o outro faz check-in | v3 |
| App | Instalável no celular (PWA) | v3 |

## Pontuação e prêmios

Proposta inicial de regras; os valores são sugestões para ajustar juntos depois de 2 a 3 semanas de uso.

| Evento | Pontos |
| --- | --- |
| Treino registrado (mínimo 30 min) | 10 |
| Bônus por intensidade alta | +5 |
| Bater a meta semanal pessoal | +20 |
| Streak de semanas com meta batida (por semana seguida) | +5, até +25 |
| Desafio cumprido | Valor definido por quem criou |
| Vencer a semana | +15 |

**Handicap (competição justa):** cada um define a própria meta semanal. O ranking compara % da meta cumprida, não volume bruto, para que níveis diferentes de treino tenham a mesma chance de ganhar.

**Regras anti-trapaça:**

- No máximo 1 treino pontuado por dia (ou 2, se definirem assim).
- Check-in só para hoje ou ontem.
- Na v2, o outro pode contestar um check-in sem foto.

**Prêmios:** os dois cadastram recompensas com custo em pontos, e os pontos são gastos ao resgatar. Exemplos:

| Prêmio | Custo sugerido |
| --- | --- |
| Escolher o filme da noite | 30 |
| Café da manhã na cama | 60 |
| Massagem | 80 |
| Jantar pago pelo outro | 150 |
| Passeio ou programa escolhido pelo vencedor | 250 |

Pontos de ranking e pontos de loja são separados: o ranking zera toda semana/mês, o saldo da loja acumula.

## Telas

Sete telas cobrem o app inteiro; as quatro primeiras são o MVP e a base para o design.

| Tela | O que mostra | Fase |
| --- | --- | --- |
| Login / cadastro | E-mail, senha, entrar | MVP |
| Home / placar | Você vs. ela na semana, % da meta, streak, botão grande de check-in | MVP |
| Check-in | Formulário rápido: tipo, duração, intensidade, foto opcional | MVP |
| Histórico | Lista de treinos dos dois, filtro por período | MVP |
| Loja de prêmios | Saldo de pontos, prêmios disponíveis, resgatar, cadastrar novo | v2 |
| Desafios e metas | Desafios ativos, criar desafio, meta semanal | v2 |
| Perfil e estatísticas | Dados pessoais, badges, gráficos de evolução | v3 |

Navegação: barra inferior fixa (Home, Histórico, Prêmios, Perfil), pensada primeiro para celular.

## Modelo de dados

Sete tabelas, todas ligadas ao usuário; as quatro primeiras bastam para o MVP.

| Tabela | Campos principais | Fase |
| --- | --- | --- |
| users | id, nome, email, senha\_hash, foto\_url, meta\_semanal, criado\_em | MVP |
| workouts | id, user\_id, data, tipo, duracao\_min, intensidade, foto\_url, observacao, criado\_em | MVP |
| point\_events | id, user\_id, workout\_id (opcional), motivo, pontos, criado\_em | MVP |
| weekly\_results | id, semana\_inicio, user\_id, pontos, pct\_meta, vencedor | MVP |
| rewards | id, criado\_por, nome, descricao, custo\_pontos, ativo | v2 |
| redemptions | id, reward\_id, user\_id, status (pedido, entregue), criado\_em | v2 |
| challenges | id, criado\_por, para\_user\_id, descricao, prazo, pontos, status | v2 |

Os pontos ficam em `point_events` (um registro por ganho ou gasto), em vez de um total salvo no usuário. Assim o saldo é sempre a soma, dá para auditar qualquer pontuação e mudar regras sem perder histórico.

## Endpoints da API

API REST em JSON; todas as rotas, exceto login e cadastro, exigem token JWT.

| Método | Rota | Função | Fase |
| --- | --- | --- | --- |
| POST | /auth/register | Criar conta | MVP |
| POST | /auth/login | Entrar e receber token | MVP |
| GET | /me | Dados do usuário logado | MVP |
| PATCH | /me | Atualizar perfil e meta semanal | MVP |
| POST | /workouts | Registrar treino (calcula pontos) | MVP |
| GET | /workouts | Listar treinos (filtros: usuário, período) | MVP |
| DELETE | /workouts/{id} | Apagar treino próprio (remove pontos) | MVP |
| GET | /scoreboard | Placar da semana ou mês | MVP |
| GET | /points/balance | Saldo de pontos da loja | v2 |
| GET / POST | /rewards | Listar e cadastrar prêmios | v2 |
| POST | /rewards/{id}/redeem | Resgatar prêmio | v2 |
| PATCH | /redemptions/{id} | Marcar prêmio como entregue | v2 |
| GET / POST | /challenges | Listar e criar desafios | v2 |
| PATCH | /challenges/{id} | Concluir ou recusar desafio | v2 |
| GET | /stats | Dados para gráficos | v3 |

## Requisitos não funcionais

O app precisa ser rápido de usar no celular: um check-in deve levar menos de 15 segundos.

- **Mobile first:** layout pensado para tela de celular, funcionando também no computador.
- **Segurança:** senhas com hash (bcrypt), HTTPS em produção, cada usuário só edita os próprios dados.
- **Fuso horário:** semanas e dias calculados em America/Sao\_Paulo, semana começando na segunda.
- **Custo:** hospedagem gratuita ou até cerca de US$ 5/mês.
- **Testes:** regras de pontuação cobertas por testes com pytest.
- **Configuração:** segredos (chave JWT, URL do banco) em variáveis de ambiente, nunca no código.
- **Idioma:** interface em português.

## Roadmap e próximos passos

Três fases, cada uma liberada quando a anterior estiver em uso de verdade.

&#91;embedded content: roadmap · 3 fases\]

Próximos passos:

- [ ] Revisar este documento com a namorada e ajustar regras de pontos e prêmios
- [ ] Desenhar as 4 telas do MVP (login, home/placar, check-in, histórico)
- [ ] Levar design + este documento para o Claude Code e criar a estrutura do projeto
- [ ] Implementar backend do MVP (auth, workouts, pontos, placar) com testes
- [ ] Implementar frontend do MVP consumindo a API
- [ ] Publicar no Render ou Railway e começar a usar
