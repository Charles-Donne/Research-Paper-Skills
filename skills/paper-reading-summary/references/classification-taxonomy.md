# Paper Classification Taxonomy

Use these fields for `metadata.json`, `retrieval.md`, Zotero tags, and optional Feishu publishing. Do not put machine-readable metadata into `note.md`.

## Core Fields

- `title`: complete official paper title.
- `authors`: author list.
- `date`: first public release date, preferably the arXiv v1 submission date for preprints, e.g. `2025-09-15`.
- `year`: optional legacy/internal year used only for compatibility and folder/index sorting when needed; do not show it in `retrieval.md` when `date` is available.
- `venue`: source or venue as recorded, e.g. arXiv, CVPR, NeurIPS.
- `publication`: preferred formal version, e.g. `CVPR 2026`, `ICLR 2025`, `Nature Machine Intelligence 2024`, `arXiv 2026`.
- `identifier`: DOI, arXiv id, OpenReview id, or publisher identifier.
- `paper_url`: official paper landing page or PDF page.
- `web_url`: project page or official website if available.
- `github_url`: code repository if available.
- `paper_type`: one of `method`, `benchmark`, `dataset`, `survey`, `theory`, `system`, `application`, `analysis`.
- `topic`: broad AI area, e.g. vision-language navigation, multimodal LLM, world model, embodied AI, 3D scene graph.
- `index_summary`: one concise retrieval sentence saying what the paper is useful for.
- `problem`, `method`, `innovation`, `significance`: compact fields extracted from `0. Concise Summary`.
- `one_sentence_summary`: one concise Chinese sentence that gives a high-level overview of the paper; this is the default Zotero Style 简记 payload, stored as a `remark:` line in Zotero `Extra`.
- `status`: `to-read`, `skimmed`, `read`, `deep-read`, `used-in-paper`, `archived`.

Section `0. Concise Summary` is the source of truth for the paper's quick-retrieval overview. Extract its structured fields into `metadata.json` and `retrieval.md`, then use those fields to inform controlled tag planning. Do not directly convert long overview sentences into tags.

## Tag Layers

Use three layers instead of one overloaded tag list:

- `domain_tags`: field labels, e.g. `embodied-ai`, `vln`, `robot-navigation`, `multimodal-llm`.
- `method_tags`: technical labels, e.g. `spatial-memory`, `topological-map`, `scene-graph`, `rl`, `diffusion`, `rag`, `prompting`.
- `project_tags`: user/project labels, e.g. `SpaceVLN-related`, `baseline`, `related-work`, `experiment-claim`, `citation-candidate`.
- `zotero_tags`: the lightweight tags to mirror into Zotero, usually only paper kind and venue/version such as `会议论文`, `ICLR 2026`.

## Quick Retrieval Entry

Use a compact paper-card format:

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
- **One-sentence summary**:

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

Do not include `Task`, `Models`, `Datasets`, `Metrics`, `Keywords`, or `Tags` in the quick index. Those belong in the full note or metadata if needed.
Keep `Title`, `Paper link`, `Web/project link`, and `GitHub link` before `## Core Content`. Put authors, publication, date, identifiers, PDF path, Zotero key, BibTeX key, and note path after `## Core Content`. Do not include tags or index-entry prose in `retrieval.md`; keep those in `metadata.json`.
