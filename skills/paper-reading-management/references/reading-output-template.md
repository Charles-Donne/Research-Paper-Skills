# Reading Note Template

```markdown
# <Paper Title>

- Title:
- Paper link:
- Web/project link:
- GitHub link:

---

## 0. Concise Summary

- **Topic** —
- **Problem** —
- **Method** —
- **Innovation** —
- **Significance** —
- **One-sentence summary**:

## 1. Motivation

## 2. Innovation

## 3. Main Content

### 3.1 Design Architecture & Methods

### 3.2 Key Algorithms & Mathematical Derivations

### 3.3 Models & Training & Dataset

### 3.4 Experimental Setup & Results

### 3.5 Technical Details

## 4. Significance and Impact

## 5. Clarifications and Simplifications

## 6. Additional Notes
```

Do not add YAML frontmatter, metadata blocks, prompt text, tags, or index entries to `note.md`. Store machine-readable fields in `metadata.json`; store the concise search card in `retrieval.md`.

Never add paper screenshots, local image files, Markdown image embeds, a `figures/` folder, or a separate figure/table appendix. Immediately after discussing a significant figure or table, keep one marker for the reader's later manual image insertion:

```markdown
<!-- figure: Figure X -->
```

```markdown
<!-- table: Table X -->
```

Do not replace or remove these markers during note integration. Do not duplicate a full figure/table list in `## 6. Additional Notes`.

Audit before handoff:

- The reading report came from one fresh isolated subagent for this paper.
- `note.md` contains exactly one `**One-sentence summary**:` line under `## 0. Concise Summary`.
- Every discussed Figure/Table has a matching nearby marker.
- Markers use exactly `<!-- figure: Figure X -->` or `<!-- table: Table X -->`.
- The note contains no Markdown image embeds or local screenshots.
