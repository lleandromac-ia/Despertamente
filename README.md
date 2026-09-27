# GeraVideos

Aplicação web para transformar **texto** (350–500 caracteres) ou **áudio .ogg** (transcrição) em vídeo narrado, com legendas na parte inferior, mídia temática (Pexels) e legenda resumida em 2 linhas editável.

## Pré-requisitos

- Python 3.11+ (testado com 3.14)
- Node.js 20+
- **FFmpeg** — no Windows: `winget install Gyan.FFmpeg`. O backend tenta achar o binário do WinGet automaticamente; se falhar, defina `FFMPEG_PATH` no `.env` (pasta `bin` que contém `ffmpeg.exe`).

## Configuração

```bash
copy .env.example .env
```

Preencha as chaves apenas no arquivo `.env` (local). **Nunca** commite chaves no `.env.example` nem no Git.

Variáveis opcionais:

- `OPENAI_API_KEY` — sugestão de 2 linhas + termos de busca (sem chave: fallback local)
- `PEXELS_API_KEY` — vídeos/fotos stock ([Pexels API](https://www.pexels.com/api/))

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

API: http://127.0.0.1:8000

## Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

## Acesso (login)

Na primeira execução é criado o administrador definido em `ADMIN_USERNAME` (padrão: `lleandromachado`) com senha `ADMIN_INITIAL_PASSWORD` (padrão: `Admin@123`). **Altere a senha após o primeiro login.**

- **Administrador:** cadastra usuários em *Usuários*.
- **Usuário comum:** edita perfil (nome, e-mail, celular, redes sociais) e **deve trocar a senha provisória** em *Perfil*.

Defina `JWT_SECRET` forte no `.env` em produção.

## Deploy na Vercel (frontend)

O **frontend** pode ir na Vercel (há `vercel.json` na raiz). Configure:

- **Root Directory:** `.` (raiz do repositório) — o `installCommand` instala deps em `frontend/`
- **Alternativa:** Root Directory = `frontend` (usa o `frontend/vercel.json`; build padrão `npm run build`)
- **Variável de ambiente:** `VITE_API_URL` = URL pública do backend (obrigatória em produção)

O **backend não roda na Vercel** (FFmpeg, Whisper, jobs longos, disco). Hospede a API em Railway, Render, Fly.io ou VPS e inclua a URL do app Vercel em `CORS_ORIGINS`.

Persistência: SQLite em `storage/app.db` — use volume persistente no provedor da API.

## Fluxo

1. Informe texto ou envie `.ogg` para transcrever (Whisper local na primeira execução baixa o modelo).
2. Ajuste o roteiro até ficar entre 350 e 500 caracteres.
3. **Sugerir legenda** → edite as 2 linhas curtas.
4. **Gerar vídeo** → narração (edge-tts PT-BR), mídia Pexels, montagem FFmpeg.

Arquivos gerados ficam em `storage/jobs/<id>/`.
