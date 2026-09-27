# GeraVideos

Aplicação web para transformar **texto** (350–500 caracteres) ou **áudio .ogg** (transcrição) em vídeo narrado, com legendas na parte inferior, mídia temática (Pexels) e legenda resumida em 2 linhas editável.

## Pré-requisitos

- Python 3.11+ (testado com 3.14)
- Node.js 20+
- **FFmpeg** no PATH ([download](https://ffmpeg.org/download.html))

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

## Fluxo

1. Informe texto ou envie `.ogg` para transcrever (Whisper local na primeira execução baixa o modelo).
2. Ajuste o roteiro até ficar entre 350 e 500 caracteres.
3. **Sugerir legenda** → edite as 2 linhas curtas.
4. **Gerar vídeo** → narração (edge-tts PT-BR), mídia Pexels, montagem FFmpeg.

Arquivos gerados ficam em `storage/jobs/<id>/`.
