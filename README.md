# Research Paper Skills

A growing collection of reusable Codex skills for academic research workflows.

The repository focuses on practical, reproducible research assistance: reading papers, producing structured summaries, organizing evidence, and synchronizing useful outputs with research tools. Each skill lives independently under `skills/` and can be installed on its own.

## Included Skills

### `paper-reading-management`

Manage an end-to-end academic paper workflow across official sources, Zotero, local reading packets, and optional Feishu/Lark publishing.

The skill enforces a reproducible reading process:

1. Resolve and verify the paper from Zotero or official sources.
2. Use one clean, independent subagent per paper.
3. Produce a structured Chinese reading report with figure/table markers.
4. Organize `note.md`, `retrieval.md`, and `metadata.json` under the Zotero collection path.
5. Audit note structure, reading isolation, and inserted figure/table files before updating the library index.
6. Keep exactly two lightweight Zotero tags by default: one paper-kind tag and one venue/source/version tag.

## Repository Layout

```text
Research-Paper-Skills/
├── README.md
├── LICENSE
├── install.sh
└── skills/
    └── paper-reading-management/
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
./install.sh paper-reading-management
```

Replace an existing installation:

```bash
./install.sh --force paper-reading-management
```

Restart the agent runtime after installation so it discovers the new skills.

## Paper Reading Management

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
Use $paper-reading-management to read this paper and generate a structured Chinese reading report.
```

```text
Use $paper-reading-management to summarize this Zotero paper and synchronize the result to Zotero.
```

The bundled reading prompt is written in English for reuse across models, while the generated reading report, including the one-sentence summary, is required to be Chinese.

The default local paper library is `~/paper`. Override it with:

```bash
export PAPER_LIBRARY_ROOT="$HOME/paper"
```

Run the diagnostic:

```bash
python3 skills/paper-reading-management/scripts/diagnose.py
```

## Zotero Style 简记

Zotero Style stores its visible **简记** value inside Zotero's `Extra` field:

```text
remark: 一句话中文概览
```

The sync helper preserves existing non-`remark:` lines such as arXiv and OpenReview identifiers and does not overwrite Zotero's abstract field:

```bash
python3 skills/paper-reading-management/scripts/zotero_sync_note.py \
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
