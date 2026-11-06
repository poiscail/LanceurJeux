# Graph Report - LanceurJeux  (2026-11-06)

## Corpus Check
- Corpus is ~1,486 words - fits in a single context window. You may not need a graph.

## Summary
- 40 nodes · 77 edges · 7 communities (2 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 4
- Community 5
- Community 6

## God Nodes (most connected - your core abstractions)
1. `App` - 11 edges
2. `scan_steam()` - 6 edges
3. `watch()` - 6 edges
4. `scan_epic()` - 4 edges
5. `running_in()` - 4 edges
6. `kv()` - 3 edges
7. `find_cover()` - 3 edges
8. `load_cover()` - 3 edges
9. `run()` - 3 edges
10. `steam_root()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `scan_epic()` --calls--> `glob`  [EXTRACTED]
  lanceur.py →   _Bridges community 6 → community 4_
- `run()` --calls--> `watch()`  [EXTRACTED]
  lanceur.py → lanceur.py  _Bridges community 2 → community 5_

## Import Cycles
- None detected.

## Communities (7 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.25
Nodes (5): fmt(), load_cover(), manual_game(), placeholder(), steam_root()

### Community 4 - "Community 4"
Cohesion: 0.60
Nodes (3): find_cover(), kv(), scan_steam()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App` connect `Community 1` to `Community 0`, `Community 5`?**
  _High betweenness centrality (0.251) - this node is a cross-community bridge._
- **Why does `watch()` connect `Community 2` to `Community 0`, `Community 1`, `Community 5`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `running_in()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._