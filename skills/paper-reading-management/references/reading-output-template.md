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

Optional figure/table appendix, add only when a useful figure/table is not already discussed and inserted in the main body:

```markdown
## 7. Figures and Tables

### 7.1 Figures

### 7.2 Tables
```

Do not add YAML frontmatter, metadata blocks, prompt text, tags, or index entries to `note.md`. Store machine-readable fields in `metadata.json`; store the concise search card in `retrieval.md`. The `One-sentence summary` line is allowed in `note.md` and is mirrored to Zotero Style 简记 as a `remark:` line in Zotero `Extra` when `zotero_sync_note.py --yes` is used.

When adding images, replace exact figure/table markers from the generated report with cropped local images:

```markdown
![Figure X](figures/fig-x.png)
```

If the report body explicitly explains a Figure/Table, insert the cropped image immediately after that paragraph. All `<!-- figure: ... -->` and `<!-- table: ... -->` markers from the generated report must be replaced before completion; leaving markers in `note.md` is an audit failure.

Put only figures/tables that are not discussed in the main body into `## 7. Figures and Tables`, split into `### 7.1 Figures` and `### 7.2 Tables`, with a short explanation for each. Avoid duplicating a full figure/table list in `## 6. Additional Notes`.

Audit before handoff:

- The reading report came from one fresh isolated subagent for this paper.
- `note.md` has exactly one `**One-sentence summary**:` line.
- Every discussed Figure/Table has a local image inserted nearby.
- Every image path exists under this paper folder.
- Cropped figure/table regions are preferred; full-page snapshots are allowed only as labeled fallbacks.
