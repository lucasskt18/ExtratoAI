# ExtratoAI

Aplicação **100% local** de finanças pessoais que transforma faturas de cartão de crédito (PDF) em um dashboard claro do mês: extrai lançamentos, categoriza gastos e permite exportar CSV — sem abrir vários apps de banco.

## O problema

Todo mês você baixa PDFs de faturas de bancos diferentes, tenta entender para onde foi o dinheiro e monta o fechamento na mão. O ExtratoAI automatiza essa leitura e centraliza a visão.

## O que ele faz

1. Recebe a fatura em PDF (upload no dashboard ou pasta `inbox` monitorada)
2. Detecta o banco e extrai as transações
3. Categoriza automaticamente (Alimentação, Assinaturas, Transporte, etc.)
4. Mostra o **total a pagar da fatura** no mês de vencimento, com lançamentos e gráfico por categoria
5. Permite corrigir categorias (e lembrar regras para próximas faturas)
6. Exporta CSV do período

## Bancos suportados

| Banco | Status | Observação |
|-------|--------|------------|
| **Nubank** | Suportado | Parser dedicado |
| **Banco Inter** | Suportado | Parser dedicado (layout `DD de mmm. AAAA`) |
| **Itaú** | Suportado | Parser dedicado (visão por ciclo/vencimento da fatura) |
| **Outros** | Fallback genérico | Pode funcionar parcialmente; resultados variam conforme o layout do PDF |
| C6 | Detectado, sem parser dedicado | Cai no fallback genérico por enquanto |

> PDFs escaneados (só imagem) ainda não são suportados — a fatura precisa ter texto selecionável.

## Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.9+, FastAPI, SQLAlchemy, SQLite |
| Extração de PDF | pdfplumber |
| Monitoramento de pasta | watchdog |
| Frontend | Vite, React, TypeScript, Tailwind CSS |
| Gráficos | Recharts |
| Exportação | CSV |

Tudo roda na sua máquina. Não há cloud, login nem telemetria no MVP.

## Como rodar localmente

### Pré-requisitos

- Python 3.9+
- Node.js 18+ (recomendado)
- macOS / Linux / Windows com terminal

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API / docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

Pastas locais:

| Pasta | Uso |
|-------|-----|
| `backend/data/inbox/` | PDFs novos (monitorada automaticamente) |
| `backend/data/uploads/` | Uploads feitos pela interface |
| `backend/data/processed/` | PDFs já processados |
| `backend/data/extratoai.db` | Banco SQLite |

### 2. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

O Vite faz proxy de `/api` para o backend na porta 8000.

### 3. Testes (opcional)

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Fixtures em `backend/tests/fixtures/`.

Para regenerar os PDFs de amostra a partir dos `.txt`:

```bash
cd backend && source .venv/bin/activate
python scripts/make_sample_pdfs.py
```

Atalhos na raiz do repo (com backend `.venv` e frontend instalados):

```bash
npm run dev:backend
npm run dev:frontend
npm test
```

## Fluxo de uso

1. Abra o dashboard e importe um PDF de fatura (ou copie o arquivo para `backend/data/inbox/`)
2. O sistema processa, categoriza e grava no SQLite
3. Navegue até o **mês de vencimento** da fatura para ver o total a pagar e todos os lançamentos do ciclo
4. Ajuste categorias se precisar (pode criar regra automática)
5. Exporte CSV quando quiser analisar em planilha

Se tentar importar o mesmo PDF de novo, o app avisa que a fatura já existe (dedupe por hash do arquivo).

## Categorias iniciais

Alimentação, Assinaturas, Transporte, Moradia, Saúde, Lazer, Compras, Educação, Outros, Não categorizado.

## Estrutura do repositório

```
ExtratoAI/
├── backend/          # FastAPI + parsers + SQLite
│   ├── app/
│   ├── data/         # inbox, uploads, processed, DB
│   ├── scripts/      # gera PDFs de fixture
│   └── tests/
├── frontend/         # React (Vite) + dashboard
├── package.json      # atalhos npm (dev/test)
└── README.md
```

## Privacidade

- Dados ficam só no seu computador (`extratoai.db` + PDFs locais)
- Sem envio para servidores externos no fluxo padrão
- Se o schema do banco mudar e o app falhar ao iniciar, apague `backend/data/extratoai.db` e reinicie o backend (as categorias seed são recriadas)

## Roadmap

**v1.1 — E-mail (IMAP)**  
Buscar anexos de fatura no Gmail/Outlook e salvar em `inbox/` (o pipeline de parsing permanece o mesmo).

**Depois**  
Mais bancos/layouts, OCR para PDF escaneado, orçamento e alertas.

Fora do MVP atual: Open Finance, app mobile, multi-usuário, sync na nuvem.
