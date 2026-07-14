# DocuSage AI Platform

**Your private AI workspace for documents.**

DocuSage helps you upload documents, get clear summaries, and ask questions about your files — all in one secure workspace. AI runs **on your machine** (no paid cloud API key required).

**Current version:** `v0.8.0`

---

## What is DocuSage for?

Use DocuSage when you want to:

- Keep important documents in one place
- Quickly understand a long file through an automatic **summary**
- **Chat** with a document (ask questions in plain language)
- Work in a clean layout with **light** or **dark** mode

Typical files: PDF, Word (DOCX), text, Markdown, and similar text-based documents.

---

## What you can do

| Action | Description |
|--------|-------------|
| **Register / Log in** | Create your own account (there is no shared default login) |
| **Add documents** | Upload files from the left-hand document list |
| **See status** | Uploaded → Processing → Ready (or Failed) |
| **Read summary** | When Ready, the right panel shows a summary of the whole document |
| **Download summary** | Save the summary as a text file |
| **Chat** | Ask follow-up questions about the selected document |
| **Trash** | Remove files to Trash, or delete permanently from Trash |
| **Theme** | Switch Light / Dark from the top bar |

---

## How to start (simple)

You need **Docker** and **Docker Compose** installed.

```bash
git clone https://github.com/PRK-Vasista/DocuSage-AI-Platform.git
cd DocuSage-AI-Platform
cp .env.example .env
# Edit .env — at minimum change SECRET_KEY for anything beyond a quick personal trial
docker compose up --build -d
```

Then open: **http://localhost:3000**

1. Register a new account  
2. Log in  
3. Add a document from the left panel  
4. Wait until status is **Ready**  
5. Read the summary and start chatting  

> First start can take a few minutes while Docker builds images and the local AI model is prepared.


---

## Limits (good to know)

| Limit | Value |
|-------|-------|
| Max size per file | 10 MB |
| Storage per account | 1 GB |
| Supported types | PDF, TXT, DOCX, MD, and other text-based files |

---

## Stopping DocuSage

```bash
docker compose down
```

To wipe all local data (users, files, and database) and start clean:

```bash
docker compose down --volumes
```

---

## Privacy note

DocuSage is designed so document AI runs **locally** in your Docker setup. You do not need a paid OpenAI (or similar) API key for the current version.

---

## For developers

Architecture, services, APIs, tests, and project history are documented separately:

→ **[developer-documentation/](./developer-documentation/)**

---

## License & copyright

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
