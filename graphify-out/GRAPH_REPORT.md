# Graph Report - Megabrain  (2026-10-26)

## Corpus Check
- 19 files · ~32,223 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 422 nodes · 1014 edges · 14 communities (9 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a6c3f7e0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- install.sh
- skill_router.py
- ui.py
- 🧠 MEGABRAIN
- Manager
- skills.py
- Roteador de skills por contexto
- HermesTest
- SkillsTest
- mac_worker.py
- ci.yml
- IntegrationsTest
- RemoteTest
- uninstall.sh

## God Nodes (most connected - your core abstractions)
1. `do_install()` - 35 edges
2. `SkillRouterTest` - 26 edges
3. `Installer` - 24 edges
4. `Manager` - 23 edges
5. `have()` - 21 edges
6. `SkillsTest` - 21 edges
7. `HermesTest` - 20 edges
8. `main()` - 19 edges
9. `route()` - 18 edges
10. `do_uninstall()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Added` --references--> `status()`  [INFERRED]
  CHANGELOG.md → lib/mac_worker.py
- `Options` --references--> `status()`  [INFERRED]
  README.md → lib/mac_worker.py
- `Tarefa 3: Adaptadores de hooks` --references--> `route()`  [INFERRED]
  docs/superpowers/plans/2026-10-26-contextual-skill-router.md → lib/skill_router.py
- `HermesTest` --uses--> `Manager`  [INFERRED]
  tests/test_hermes.py → lib/integrations.py
- `IntegrationsTest` --uses--> `Manager`  [INFERRED]
  tests/test_integrations.py → lib/integrations.py

## Import Cycles
- None detected.

## Communities (14 total, 5 thin omitted)

### Community 0 - "install.sh"
Cohesion: 0.12
Nodes (60): abort_ui(), agent_probe(), ask_toggle(), ask_yes_no(), cmd_help(), cmd_mark_installed(), cmd_status(), cmd_sync() (+52 more)

### Community 1 - "skill_router.py"
Cohesion: 0.10
Nodes (24): default_roots(), ExternalCandidate, extract_search_terms(), format_context(), handle_hook(), invalidate_skill_index(), load_config(), main() (+16 more)

### Community 2 - "ui.py"
Cohesion: 0.07
Nodes (24): energize(), frame(), jitter(), prepare(), pulse(), alive(), bar_text(), bottom_rows() (+16 more)

### Community 3 - "🧠 MEGABRAIN"
Cohesion: 0.05
Nodes (39): [1.0.0] - 2026-10-13, [1.0.1] - 2026-10-13, [1.0.2] - 2026-10-20, [1.1.0] - 2026-10-22, [1.2.0] - 2026-10-22, [1.3.0] - 2026-10-26, Added, Added (+31 more)

### Community 4 - "Manager"
Cohesion: 0.13
Nodes (7): Tarefa 4: Instalação, remoção e CLI local, main(), Manager, digest(), exists(), Installer, main()

### Community 5 - "skills.py"
Cohesion: 0.14
Nodes (6): main(), ssh_request(), download_collection(), download_source(), excluded(), normalize_skill()

### Community 6 - "Roteador de skills por contexto"
Cohesion: 0.07
Nodes (25): Arquivos e responsabilidades, Focos de revisão, Restrições globais, Revisão final do plano, Roteador de skills por contexto: plano de implementação, Tarefa 1: Roteamento local e política de esforço, Tarefa 2: Busca externa temporária e cache, Tarefa 3: Adaptadores de hooks (+17 more)

### Community 9 - "mac_worker.py"
Cohesion: 0.26
Nodes (12): command_output(), dispatch(), doctor(), job_dir(), now(), owns_runner(), parse_events(), read_tail() (+4 more)

### Community 10 - "ci.yml"
Cohesion: 0.12
Nodes (15): runs-on, steps, timeout-minutes, jobs, checks, name, permissions, contents (+7 more)

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `status()` connect `mac_worker.py` to `🧠 MEGABRAIN`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `SkillRouterTest` (e.g. with `ExternalCandidate` and `RouterConfig`) actually correct?**
  _`SkillRouterTest` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `install.sh` be split into smaller, more focused modules?**
  _Cohesion score 0.12211538461538461 - nodes in this community are weakly interconnected._
- **Why does `Options` connect `🧠 MEGABRAIN` to `mac_worker.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Installer` (e.g. with `Manager` and `HermesTest`) actually correct?**
  _`Installer` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `skill_router.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09760374050263004 - nodes in this community are weakly interconnected._
- **Are the 6 inferred relationships involving `Manager` (e.g. with `Installer` and `HermesTest`) actually correct?**
  _`Manager` has 6 INFERRED edges - model-reasoned connections that need verification._