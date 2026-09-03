# Optional Feishu/Lark Sync

Use Feishu/Lark only when the user asks to publish, mirror, share, or back up paper notes to cloud documents.

## Local-First Principle

Keep the local folder as the source of truth:

- `metadata.json`: machine-readable metadata.
- `note.md`: full reading note.
- `retrieval.md`: quick index card.
- Zotero item/PDF path: bibliography and PDF source of truth.

Feishu should mirror or publish selected content, not replace the local library.

Default local root: `${PAPER_LIBRARY_ROOT:-$HOME/paper}`. Use a project-specific root only when the user or project instructions explicitly request it.

## Recommended Cloud Shape

Create or update one Feishu doc per paper:

```text
Paper Reading/
  <Year>/
    <Paper Title>
```

The Feishu doc should include:

- Metadata table.
- Concise summary.
- Motivation and innovation.
- Main content.
- Important figure/table discussion and manual insertion markers.
- Quick retrieval fields.
- Local folder path and Zotero item key.
- No generated or embedded figure/table screenshots; the reader may add them manually after review.

## Tooling

When the user asks for Feishu sync, use the Lark document skill:

- Create or update docs with `lark-doc`.
- Search existing cloud docs before creating duplicates.
- If importing local Markdown or organizing cloud folders/files is needed, use `lark-drive`.

## One-Command Mirror

Use the local helper first. It searches existing Feishu/Lark docs by paper title, updates `metadata.feishu_doc_token` documents when present, creates a new doc when no exact match is found, and writes `feishu_doc_token`, `feishu_doc_url`, and `feishu_synced_at` back to `metadata.json` after a confirmed sync.

Plan only, no cloud write:

```bash
python3 <skill-dir>/scripts/feishu_sync.py \
  --paper-folder "<paper-folder>"
```

Create or overwrite after confirming the target:

```bash
python3 <skill-dir>/scripts/feishu_sync.py \
  --paper-folder "<paper-folder>" \
  --yes
```

To force a specific existing document:

```bash
python3 <skill-dir>/scripts/feishu_sync.py \
  --paper-folder "<paper-folder>" \
  --doc "<doc-url-or-token>" \
  --yes
```

To create under a known parent folder or wiki node:

```bash
python3 <skill-dir>/scripts/feishu_sync.py \
  --paper-folder "<paper-folder>" \
  --parent-token "<folder-or-wiki-node-token>" \
  --yes
```

Do not publish to Feishu without explicit user confirmation of destination and content scope.
