# Research Paper Skills

A growing collection of reusable Codex skills for academic research workflows.

The repository focuses on practical, reproducible research assistance: reading papers, producing structured summaries, organizing evidence, and synchronizing useful outputs with research tools. Each skill lives independently under `skills/` and can be installed on its own.

## Included Skills

### `paper-reading-summary`

Quickly understand academic papers and generate structured Chinese reading notes that support both rapid retrieval and deep study.

The skill produces a two-level reading result:

1. **Quick overview and retrieval layer**: Section `0. Concise Summary` explains the paper through `Topic`, `Problem`, `Method`, `Innovation`, `Significance`, and a one-sentence Chinese overview.
2. **Detailed reading layer**: Sections `1–6` explain motivation, innovations, methods, algorithms, models, training, datasets, experiments, technical details, impact, limitations, simplifications, related work, and important figures/tables.

Section `0` is the retrieval hub for each paper. Its structured fields are extracted into `metadata.json` and `retrieval.md` for fast search, comparison, classification, and tag planning. The one-sentence overview can also be synchronized to Zotero Style's visible **简记** field.

Synchronization and organization are downstream conveniences. The primary purpose is to read a paper quickly, understand it deeply, and preserve the result as a reusable reading note.

## Repository Layout

```text
Research-Paper-Skills/
├── README.md
├── LICENSE
├── install.sh
└── skills/
    └── paper-reading-summary/
        ├── SKILL.md
        ├── agents/
        ├── references/
        └── scripts/
```

Additional research skills can be added under `skills/` without changing the repository structure.

## Requirements

Basic use:

- Codex or another agent runtime that supports `SKILL.md` skills.
- Python 3.9 or newer.

Optional integrations:

- Zotero Desktop with its local API enabled for Zotero reads.
- A Zotero MCP write bridge for Zotero metadata and tag writes.
- Zotero Style to display the `remark:` value as **简记**.
- `pypdf` or `pdfplumber` for PDF-related helpers.
- `lark-cli` for optional Feishu/Lark synchronization.

Default Zotero endpoints:

```bash
export ZOTERO_LOCAL_API_URL="http://127.0.0.1:23119"
export ZOTERO_MCP_URL="http://127.0.0.1:23120/mcp"
```

## Installation

Clone the repository:

```bash
git clone https://github.com/Charles-Donne/Research-Paper-Skills.git
cd Research-Paper-Skills
```

Install every skill in the repository:

```bash
./install.sh
```

Install only the paper-reading skill:

```bash
./install.sh paper-reading-summary
```

Replace an existing installation:

```bash
./install.sh --force paper-reading-summary
```

Restart the agent runtime after installation so it discovers the new skills.

## Paper Reading And Summary

### Reading Note Structure

Every complete reading note follows this structure:

```text
0. Concise Summary
   Topic · Problem · Method · Innovation · Significance
   One-sentence summary
1. Motivation
2. Innovation
3. Main Content
   3.1 Design Architecture & Methods
   3.2 Key Algorithms & Mathematical Derivations
   3.3 Models & Training & Dataset
   3.4 Experimental Setup & Results
   3.5 Technical Details
4. Significance and Impact
5. Clarifications and Simplifications
6. Additional Notes
```

The note is designed for two reading speeds:

- Read only Section `0` to quickly decide whether the paper is relevant.
- Read Sections `1–6` for a detailed understanding of the paper and its evidence.

### Reading Packet

Each organized paper can produce:

| Artifact | Purpose |
| --- | --- |
| `note.md` | Complete structured reading note covering Sections `0–6`. |
| `retrieval.md` | Compact search card extracted from Section `0`, plus bibliographic metadata. |
| `metadata.json` | Machine-readable metadata, core overview fields, layered tags, status, and integration identifiers. |
| `figures/` | Optional important figure and table snapshots inserted near the relevant explanations. |
| `INDEX.md` | Minimal library-level directory for navigating organized papers. |

Section `0` supplies the core retrieval fields stored in `retrieval.md` and `metadata.json`. These fields also inform domain, method, and project tag planning; tags are kept separately so they remain concise and controllable.

### Core Workflow

1. Resolve the paper from Zotero, a local PDF, or an official web source.
2. Verify bibliographic metadata and official project/code links.
3. Read the full paper and generate a structured Chinese note covering Sections `0–6`.
4. Extract Section `0` into reusable retrieval and metadata records.
5. Optionally synchronize the one-sentence overview, lightweight tags, folders, and cloud documents.

Example prompts:

```text
Use $paper-reading-summary to read this paper and generate a structured Chinese reading report.
```

```text
Use $paper-reading-summary to summarize this Zotero paper and synchronize the result to Zotero.
```

The bundled reading prompt is written in English for reuse across models, while the generated reading report, including the one-sentence summary, is required to be Chinese.

The default local paper library is `~/paper`. Override it with:

```bash
export PAPER_LIBRARY_ROOT="$HOME/paper"
```

Run the diagnostic:

```bash
python3 skills/paper-reading-summary/scripts/diagnose.py
```

## Zotero Style 简记

Zotero Style stores its visible **简记** value inside Zotero's `Extra` field:

```text
remark: 一句话中文概览
```

The sync helper preserves existing non-`remark:` lines such as arXiv and OpenReview identifiers and does not overwrite Zotero's abstract field:

```bash
python3 skills/paper-reading-summary/scripts/zotero_sync_note.py \
  --paper-folder "<paper-folder>" \
  --sync-tags \
  --yes
```

## Adding Skills

Place each new skill in its own directory:

```text
skills/<skill-name>/SKILL.md
```

Keep skill-specific scripts and references inside that directory. The root installer automatically discovers skill directories containing `SKILL.md`.

## Security

Do not commit API keys, Zotero profiles, paper PDFs, generated reading libraries, or private research data.

## License

MIT
