# Literal archive formatting boundary

The byte-identical historical `Project_Visualizer.py` copy contains inherited trailing whitespace. An unrestricted `git diff --cached --check` reports that whitespace in `inputs/HISTORICAL_THEME_GENERATOR_SOURCE.py`. It is retained deliberately: rewriting a literal source archive for style would break its authoritative payload hash.

Authored review scripts and documentation are checked separately with the literal `inputs/` archive excluded. No current repository code is exempted or edited. Numerical, map-stream, rendered-pixel and preservation assertions are unchanged. The full source copy remains traceable to its original Git commit and SHA256.

Large derived artwork-inspection JSON is stored via Git LFS; small decision/provenance/QA records remain plain text. Original archived text is not newline-normalized.
