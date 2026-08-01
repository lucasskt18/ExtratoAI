# ExtratoAI

Aplicação **local** para extrair faturas de cartão (PDF), categorizar gastos e visualizar um dashboard do mês.

## Stack

- **Backend:** Python, FastAPI, SQLite, pdfplumber, watchdog
- **Frontend:** Vite, React, TypeScript, Tailwind, Recharts
- **Parsers MVP:** Nubank + Banco Inter (+ fallback genérico)
- **Export:** CSV

## Como rodar

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000/docs

Pasta monitorada automaticamente:

`backend/data/inbox/`

PDFs processados vão para `backend/data/processed/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://127.0.0.1:5173

### Testes

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Fixtures de texto/PDF em `backend/tests/fixtures/`.

## Fluxo

1. Arraste um PDF no dashboard **ou** copie para `backend/data/inbox/`
2. O backend extrai o texto, detecta o banco, parseia transações e categoriza
3. O dashboard atualiza totais, gráfico por categoria e lista editável
4. Corrija categorias (opcionalmente cria regra de merchant)
5. Exporte CSV do mês

## Categorias seed

Alimentação, Assinaturas, Transporte, Moradia, Saúde, Lazer, Compras, Educação, Outros, Não categorizado.

## Roadmap v1.1 — E-mail (IMAP)

O pipeline de parsing permanece o mesmo. A próxima etapa só muda a **fonte do PDF**:

1. Configurar credenciais IMAP (Gmail App Password / Outlook) em `.env`
2. Worker periódico (`imaplib` ou `aioimaplib`) busca mensagens de remetentes conhecidos (`fatura@nubank.com.br`, etc.)
3. Baixar anexos `.pdf` para `data/inbox/`
4. O watcher existente processa normalmente

Não entra no MVP atual: OAuth cloud, sync remoto, multi-usuário.

## Privacidade

Tudo roda na sua máquina. Sem telemetria. O banco é o arquivo SQLite em `backend/data/extratoai.db`.
