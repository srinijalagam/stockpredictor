# Deploying to Hugging Face Spaces

This folder holds everything **specific to the Hugging Face (HF) Space**. The
agent (`agent/`) and UI (`ui/`) sources are reused as-is — the deploy script
assembles them into a single-container Docker Space.

## How it fits together

```
hf-space/
├─ Dockerfile     # builds the UI, then serves UI + API on port 7860
├─ serve.py       # FastAPI entrypoint: mounts static UI on top of the agent API
├─ README.md      # becomes the Space's README (HF front matter: sdk=docker)
├─ deploy.ps1     # Windows deploy: assembles ./build and git-pushes to HF
├─ deploy.sh      # Linux/macOS/WSL equivalent
└─ build/         # generated, git-ignored working tree pushed to the Space
```

One container serves both: `serve.py` imports the agent's FastAPI app (so
`/api/*` and `/health` work) and adds the built React UI as static files with an
SPA fallback. No nginx needed in the Space.

## One-time setup

1. **Create / sign in** to a Hugging Face account: https://huggingface.co/join
2. **Create a WRITE token**: https://huggingface.co/settings/tokens
   → "Create new token" → type **Write** → copy it (`hf_...`).

## Deploy

Windows PowerShell:

```powershell
$env:HF_TOKEN = "hf_xxx"
./hf-space/deploy.ps1 -Space "your-username/stock-predictor"
```

Linux / macOS / WSL:

```bash
export HF_TOKEN=hf_xxx
./hf-space/deploy.sh your-username/stock-predictor
```

The Space is created automatically on first push and starts building.

## Set the keys as Space secrets (do NOT commit `.env`)

In the Space: **Settings → Variables and secrets** → add:

| Name              | Kind     | Value (example)                                                  |
| ----------------- | -------- | ---------------------------------------------------------------- |
| `OPENAI_API_KEY`  | secret   | your (rotated) Gemini key                                        |
| `OPENAI_BASE_URL` | secret   | `https://generativelanguage.googleapis.com/v1beta/openai/`       |
| `OPENAI_MODEL`    | variable | `gemini-2.5-flash`                                               |
| `TAVILY_API_KEY`  | secret   | optional — better grounded search                                |

After adding secrets the Space rebuilds. When it shows **Running**, share the
public URL `https://huggingface.co/spaces/your-username/stock-predictor` for
people to test.

## Notes

- **Cost:** HF CPU Spaces are free (they sleep when idle; first hit cold-starts).
  Staying on Gemini's free tier keeps LLM cost at $0 within rate limits.
- **Updating:** re-run the deploy script after code changes; it force-pushes the
  latest assembled tree.
- **Security:** never push real keys. The generated `build/.gitignore` excludes
  `.env`; keys belong in Space secrets only.
