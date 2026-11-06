# Graph Report - LanceurJeux  (2026-11-06)

## Corpus Check
- Corpus is ~759 words - fits in a single context window. You may not need a graph.

## Summary
- 28 nodes · 48 edges · 6 communities (1 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 2
- Community 4
- Community 5

## God Nodes (most connected - your core abstractions)
1. `App` - 8 edges
2. `scan_steam()` - 5 edges
3. `scan_epic()` - 4 edges
4. `running_in()` - 4 edges
5. `kv()` - 3 edges
6. `fmt()` - 3 edges
7. `steam_root()` - 2 edges
8. `Lanceur de jeux unifié : Steam, Epic, jeux ajoutés à la main. Temps de jeu par…` - 1 edges
9. `Vrai si un processus tourne depuis ce dossier.` - 1 edges

## Surprising Connections (you probably didn't know these)
- `scan_steam()` --calls--> `glob`  [EXTRACTED]
  lanceur.py →   _Bridges community 2 → community 5_

## Import Cycles
- None detected.

## Communities (6 total, 5 thin omitted)

### Community 2 - "Community 2"
Cohesion: 0.50
Nodes (3): kv(), scan_steam(), steam_root()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App` connect `Community 0` to `Community 1`, `Community 2`?**
  _High betweenness centrality (0.275) - this node is a cross-community bridge._
- **Why does `running_in()` connect `Community 4` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `fmt()` connect `Community 0` to `Community 1`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._