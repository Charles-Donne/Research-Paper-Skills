# Research Paper Skills

A growing collection of reusable Codex skills for academic research workflows.

The repository focuses on practical, reproducible research assistance: reading papers, producing structured summaries, organizing evidence, and synchronizing useful outputs with research tools. Each skill lives independently under `skills/` and can be installed on its own.

## Included Skills

### `paper-reading-summary`

Read academic papers and produce structured Chinese reading reports and concise summaries.

Core capabilities:

- Resolve papers from Zotero, local PDFs, or official web sources.
- Verify bibliographic metadata and official project/code links.
- Generate detailed Chinese reading reports from a reusable English prompt.
- Extract concise `Topic`, `Problem`, `Method`, `Innovation`, and `Significance` summaries.
- Create reproducible local reading packets containing `note.md`, `retrieval.md`, and `metadata.json`.
- Synchronize the one-sentence Chinese summary to Zotero Style's visible **简记** field.
- Optionally synchronize lightweight tags, collection-aligned folders, and Feishu/Lark documents.

Synchronization and organization are downstream conveniences. The skill's primary purpose is paper reading, understanding, and summarization.

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
