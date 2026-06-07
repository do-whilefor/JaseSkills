# import/export/download → path traversal → arbitrary file read/write candidate

硬规则：never read real secrets; use harmless local marker files only.
