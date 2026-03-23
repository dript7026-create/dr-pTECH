# ClipConceptBook Format

`ClipConceptBook` uses the `.ccp` extension.

Current base format:
- Magic: `CCP1`
- Header: fixed-size `CCBHeader`
- Manifest payload: UTF-8 JSON
- Source payload: raw bytes of the original page zip

Expected source zip contents:
- `.clip` files named with `pg1`, `pg2`, ... `pgn` ordering.
- Nested directories are allowed, but the basename still has to match the `pgN.clip` convention.

Manifest contents:
- `title`
- `book_mode`
- `page_naming`
- `source_zip`
- `page_count`
- `pages[]`
- optional `prompt_map`

Design intent:
- A `.ccp` is a packaged, ordered concept-book source container.
- At this stage, `.clip` files are treated as opaque authored page assets and ordered chronologically.
- Interactivity, animation, or game-page behavior is expected to be described through the embedded prompt map and future Clip Studio scripting metadata.

Prompt map intent:
- The packager can embed a JSON prompt map file directly into the `.ccp` manifest.
- That prompt map is what later Recraft tooling will translate into standard image-generation manifest entries.