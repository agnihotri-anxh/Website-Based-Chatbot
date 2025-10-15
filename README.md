## Sybrant Chatbot Assignment

A Flask-based chatbot for Sybrant Technologies with appointment booking, Pinecone-powered retrieval, and email confirmations.

### Requirements
- Python 3.11
- MongoDB (Atlas or local)
- Pinecone account and API key (optional; leave empty to disable)
- SMTP credentials for sending emails

### Setup
1. Create and activate a virtual environment.
2. Copy `ENV.example` to `.env` and fill values.
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the app (dev):
```bash
python wsgi.py
```
App listens on `http://localhost:5000`.

### Environment Variables
See `ENV.example` for all options. Key ones:
- `MONGODB_URI`: Mongo connection string
- `PINECONE_API_KEY`: Pinecone API key
- `MAIL_USERNAME`, `MAIL_PASSWORD`: SMTP credentials

### Endpoints
- `/` Chat UI
- `/chat` POST JSON { message, session_id }
- `/admin` Appointments UI
- `/appointments` JSON list of appointments
- `/appointments/<id>` JSON details
- `/ingest` POST to ingest links from `essential_links.txt`

### Docker
Build and run:
```bash
docker build -t sybrant-chatbot .
docker run -p 5000:5000 --env-file .env sybrant-chatbot
```

### Notes
- No secrets are committed. Configure via environment variables.
- Pinecone is optional; the app runs without it.
- Logging uses structured INFO-level output.


## Deploying on Vercel

This project includes a serverless entry for Vercel using `@vercel/python`.

### Files added
- `vercel.json` — routes all endpoints to `api/index.py`
- `api/index.py` — exposes `app` from Flask and forces `CLOUD_MODE=true`
- `requirements-vercel.txt` — lightweight deps (no torch/embeddings)

### Environment variables (Vercel Project Settings → Environment Variables)
- `CLOUD_MODE=true`
- `GROQ_API_KEY=<your_groq_key>`
- `GROQ_MODEL=llama-3.1-70b-versatile` (default)
- `MONGODB_URI=<your_mongodb_uri>`
- `MONGODB_DB=sybrantbot`
- `MONGODB_COLLECTION=appointments`
- `MAIL_SERVER=smtp.gmail.com`
- `MAIL_PORT=587`
- `MAIL_USE_TLS=true`
- `MAIL_USERNAME=<smtp_user>`
- `MAIL_PASSWORD=<smtp_pass>`
- `MAIL_DEFAULT_SENDER=<from_email>`

Pinecone is disabled in `CLOUD_MODE`. If you need RAG on Vercel, prefer an external API service; otherwise re-enable Pinecone and add its env vars.

### Deploy steps
1. Install Vercel CLI and login:
   ```bash
   npm i -g vercel
   vercel login
   ```
2. Link and set Python build to use `requirements-vercel.txt`:
   ```bash
   vercel link
   vercel env pull .env.local  # optional
   ```
3. Configure your project (Settings → Build & Development Settings):
   - Build Command: not required (serverless)
   - Output Directory: not required
   - Install Command: `pip install -r requirements-vercel.txt`
4. Set environment variables listed above in Vercel Project Settings.
5. Deploy:
   ```bash
   vercel --prod
   ```

After deploy, open the URL and test `/` and `/chat`.


