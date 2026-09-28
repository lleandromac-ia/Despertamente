# Deploy: [despertamente.vercel.app](https://despertamente.vercel.app)

O site na Vercel é **somente o frontend**. Login e vídeos exigem a **API FastAPI** em outro host.

## 1. Frontend (já na Vercel)

Projeto: **https://despertamente.vercel.app**

Após a API estar no ar, em **Vercel → Settings → Environment Variables**:

| Variável | Valor |
|----------|--------|
| `VITE_API_URL` | URL pública da API, ex. `https://despertamente-api.onrender.com` |

Salve e faça **Redeploy** (Build). Sem redeploy, o login continua com HTTP 405.

## 2. Backend (Render com Docker)

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → repo `Despertamente`.
2. Preencha secrets: `ADMIN_INITIAL_PASSWORD`, `OPENAI_API_KEY`, `PEXELS_API_KEY`.
3. Anote a URL do serviço (ex. `https://despertamente-api.onrender.com`).
4. Teste: `GET https://SUA-API/api/health` → JSON `{ "ok": true, ... }`.

Arquivo: [`render.yaml`](render.yaml) + [`Dockerfile`](Dockerfile) (inclui FFmpeg).

Alternativas: Railway, Fly.io, VPS com Docker.

## 3. CORS

No backend, `CORS_ORIGINS` deve incluir:

```text
https://despertamente.vercel.app
```

(Já sugerido no `render.yaml`.)

## 4. Login padrão

- Usuário: `lleandromachado`
- Senha: valor de `ADMIN_INITIAL_PASSWORD` no Render (padrão local: `Admin@123` no `.env`).

## 5. Desenvolvimento local

```powershell
# Terminal 1
cd backend
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm run dev
```

Acesse http://localhost:5173 (proxy `/api` → 8000).
