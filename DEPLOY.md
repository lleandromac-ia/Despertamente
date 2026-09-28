# Deploy: [despertamente.vercel.app](https://despertamente.vercel.app)

O site na Vercel é **somente o frontend**. Login e vídeos exigem a **API FastAPI** em outro host.

## 1. Frontend (já na Vercel)

Projeto: **https://despertamente.vercel.app**

Após a API estar no ar, em **Vercel → Settings → Environment Variables**:

| Variável | Valor |
|----------|--------|
| `VITE_API_URL` | URL pública da API, ex. `https://despertamente-api.onrender.com` |

Salve e faça **Redeploy** (Build). Sem redeploy, o login continua com HTTP 405.

## 2. Backend (Render com Docker) — **obrigatório para login na Vercel**

Hoje a URL `https://despertamente-api.onrender.com` só funciona **depois** que o serviço existir no Render.  
Enquanto `/api/health` devolver **Not Found**, o login na Vercel **não vai funcionar** (não é bug do frontend).

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
2. Conecte o repo GitHub **`lleandromac-ia/Despertamente`** (branch `main`).
3. Aplique o blueprint (`render.yaml`, plano **free**, serviço **`despertamente-api`**).
4. Preencha secrets obrigatórios: **`ADMIN_INITIAL_PASSWORD`**, e opcionalmente `OPENAI_API_KEY`, `PEXELS_API_KEY`.
5. Aguarde status **Live** (primeiro build Docker pode levar ~10–15 min).
6. Teste no navegador: `https://despertamente-api.onrender.com/api/health` → JSON `{ "ok": true, ... }`.  
   Se aparecer **404** ou `x-render-routing: no-server`, o serviço **ainda não existe** — não adianta redeploy na Vercel.
7. Na Vercel, confirme `VITE_API_URL=https://despertamente-api.onrender.com` e faça **Redeploy** do frontend.

### Erro "Failed to fetch" no login

- `VITE_API_URL` na Vercel aponta para `https://despertamente-api.onrender.com` (sem `/` no final).
- A API precisa estar **Live** no Render. URL configurada sem servidor = navegador bloqueia (CORS) e mostra *Failed to fetch*.
- Confirme: https://despertamente-api.onrender.com/api/health abre JSON no navegador.

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
