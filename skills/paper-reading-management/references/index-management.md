# Local Index Management

Default root:

```text
${PAPER_LIBRARY_ROOT:-$HOME/paper}/
```

Recommended structure mirrors the primary Zotero collection path:

```text
${PAPER_LIBRARY_ROOT:-$HOME/paper}/
  INDEX.md
  <Zotero top collection>/
    <Zotero child collection>/
      <short-title>--<publication-year>/
        metadata.json
        note.md
        retrieval.md
        figures/
```

Example:

```text
${PAPER_LIBRARY_ROOT:-$HOME/paper}/
  INDEX.md
  VLN/
    Classic/
      vision-language-navigation--cvpr2018/
        metadata.json
        note.md
        retrieval.md
        figures/
```

## Zotero Collection Mapping

Use the paper's primary Zotero collection path as the local parent directory. If a paper belongs to multiple Zotero collections, choose the deepest collection path as the primary local path and keep the other collection memberships in Zotero.

Get the primary path with:

```bash
python3 <skill-dir>/scripts/zotero_collection_path.py <zotero-item-key> --first
```

If the item is not in any collection, use `Unfiled`.

## File Roles

- `metadata.json`: machine-readable record for scripts and optional sync; not meant for daily reading.
- `note.md`: the full human reading note produced from the mandatory subagent reading report.
- `retrieval.md`: optional per-paper quick retrieval card with publication information, official links, and the one-sentence retrieval cue.
- `figures/`: optional screenshots cropped/rendered from the Zotero PDF and embedded in `note.md`.
- `INDEX.md`: root tree directory only. Keep it minimal: Zotero collection path plus paper short title/version linking to `note.md`.

## Naming

Use:

```text
<Zotero collection path>/<short-title>--<publication-year>/
```

Examples:

```text
VLN/Classic/vision-language-navigation--cvpr2018/
Embodied AI/Object Navigation/vlfm--icra2024/
```

Use Zotero `shortTitle` when available; otherwise derive a short slug from the full title. For the suffix, prefer formal publication/version such as `cvpr2026`, `iclr2025`, `arxiv2024`.

## Retrieval Entry Format

Use this compact format in per-paper `retrieval.md`; root `INDEX.md` should not duplicate these details:

```markdown
# <Short Title>

- Title:
- Paper link:
- Web/project link:
- GitHub link:

## Core Content

- **Topic**:
- **Problem**:
- **Method**:
- **Innovation**:
- **Significance**:

## Bibliographic Metadata

- Authors:
- Publication:
- Date:
- Identifier:
- PDF:
- Zotero:
- BibTeX:
- Note:
```

Do not include `Task`, `Models`, `Datasets`, `Metrics`, `Keywords`, or `Tags` in the quick index.

## Root INDEX.md Format

Keep `INDEX.md` as a concise tree:

```markdown
# Paper Directory

## VLN/Classic

- [Vision-and-Language Navigation](VLN/Classic/vision-language-navigation--cvpr2018/note.md) (CVPR 2018)
```

Do not include paper links, GitHub links, Zotero keys, folder paths, or index-entry text in `INDEX.md`; those belong in `retrieval.md` or `metadata.json`.

## Index Updates

`organize_paper.py` updates root `INDEX.md` automatically unless `--no-index` is passed.

To rebuild manually:

```bash
python3 <skill-dir>/scripts/update_index.py "${PAPER_LIBRARY_ROOT:-$HOME/paper}"
```
