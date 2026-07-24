# Obsidian And Dataview Convention

Obsidian is optional. Markdown files remain portable, and metadata stays in `metadata.json` so the human reading report stays clean.

## File Layout

Default per-paper layout:

```text
${PAPER_LIBRARY_ROOT:-$HOME/paper}/
  INDEX.md
  <Zotero top collection>/
    <Zotero child collection>/
      <short-title>--<publication-year>/
        metadata.json
        note.md
        retrieval.md  # optional
        figures/
```

Use Zotero as the paper/PDF library. Use `note.md` as the human reading note, `retrieval.md` as an optional compact search card, and `figures/` only for selected figure/table screenshots inserted into notes.

## Dataview Metadata Source

Do not include YAML frontmatter in `note.md` or `retrieval.md` for this workflow. If Dataview is used, point it at generated sidecar metadata or a separately generated index file derived from `metadata.json`, keeping field names stable:

```json
{
  "type": "paper-reading",
  "title": "...",
  "date": "2025-09-15",
  "publication": "CVPR 2026",
  "status": "deep-read",
  "paper_type": "method",
  "topic": "embodied AI",
  "paper_pdf": "/Users/.../Zotero/storage/.../paper.pdf"
}
```

Obsidian/Dataview integration is optional and should never change the shape of `note.md`.

## Dataview Examples

If a Dataview layer is later generated, typical queries can use fields like `publication`, `date`, `paper_type`, and `status`.

## Recommendation

Use Obsidian/Dataview as an optional local UI layer. Do not make it a hard dependency: the skill should still work with plain Markdown and JSON. Keep Zotero as the source of truth for PDFs and bibliography.
