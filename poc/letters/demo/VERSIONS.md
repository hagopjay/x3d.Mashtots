# Letter Constellation: versions

Every version is kept as built, in its own folder, and is never edited after it is published. A new design is a new folder and a new private
preview. Each page from v1 on carries a versions strip that links its siblings.

| version | date | what | built from | private preview |
|---|---|---|---|---|
| [v0](v0/index.html) | 15-16 Nov 2026 | First sky: 36 learned stars from the core mashtots-40M model, Օ Ֆ և placed by hand, five-sets finding (50% vs 6% by chance, p 0.0002, Measured) | `constellation.py --export core_export_g4a.json` | https://claude.ai/artifact/CgcduzE3HAPXwcM1MYea9m |
| [v1](v1/index.html) | 16 Nov 2026 | The galaxy edition: every letter is a star (768 px bold-ink glyph with a metal rim: gold for Mashtots' 36, silver for Օ Ֆ, copper for և), a constellation (its own font outline as a star chart) and a galaxy (arms = numeral row, size = letter counts, Measured; Օ Ֆ elliptical, և two merging). 39 OKLCH palettes, sound sets own a colour band and a ring. Same learned layout and finding as v0. Three build passes, each reviewed by a four-lens critic panel (art, X3D, layout, data honesty). | `galaxy.py --export core_export_g4a.json.gz` | https://claude.ai/artifact/Lro8eNic3DFyvDxWJRw9G5 |

`core_export_g4a.json.gz` is the core run's model export (run g4a, 15 Nov 2026), kept so every version can be rebuilt (`gunzip -k` it first).
To view a version locally, serve its folder with a UTF-8 static server (Python's plain `http.server` sends no charset and the Armenian keys break).
