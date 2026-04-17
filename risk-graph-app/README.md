# risk-graph-app

Local-only macOS Python app for planning branching futures with catastrophic-risk-averse scoring.

## What this app does

- Models decisions, events, actors, outcomes, positive terminals, and catastrophic terminals.
- Supports branch coexistence, hard forks (exclusive per path), shared-state dependencies, escalation chains, and bounded loops.
- Evaluates each starting decision across full reachable future states.
- Ranks top 3 safest decisions (lower score is better) with catastrophe dominance.
- Renders graph via Graphviz (SVG/PNG).
- Provides a local browser editor for easier authoring while JSON remains canonical storage.

No cloud, no LLM, no database, no YAML, no frontend build tool.

## Requirements

- Python 3.11+
- Graphviz binary installed (`brew install graphviz`)
- Python package: `graphviz`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI commands

Existing:

```bash
python main.py validate scenarios/example_scenario.json
python main.py evaluate scenarios/example_scenario.json
python main.py render scenarios/example_scenario.json --format svg
python main.py render scenarios/example_scenario.json --format png
python main.py report scenarios/example_scenario.json
```

New:

```bash
python main.py validate scenarios/draft_example.json --mode draft
python main.py edit scenarios/example_scenario.json
python main.py new-draft scenarios/my_draft.json
python main.py new-draft scenarios/my_draft.json --open-editor
```

## Strict vs draft mode

### Strict mode

- Enforces complete required fields.
- Incomplete nodes/edges are errors.
- Intended for reliable evaluate/render/report runs.

### Draft mode

- Allows incomplete items during authoring.
- Incomplete edges are warnings and saved in JSON.
- Evaluator skips incomplete edges and may skip unevaluable decisions.
- Report explicitly lists skipped/incomplete/guessed details.

## Draft semantics

Supported draft fields (optional, backward compatible):

- `scenario.mode`: `strict | draft`
- `scenario.metadata`: object
- `scenario.editor`: object
- `node.draft_status`: `complete | incomplete | guessed`
- `node.draft_note`: string
- `edge.draft_status`: `complete | incomplete | guessed`
- `edge.draft_note`: string

Backward compatibility: old files without these fields still load and evaluate.

## Editor usage

Run:

```bash
python main.py edit scenarios/example_scenario.json
```

Editor features:

- Load scenario
- Save strict / Save draft
- Add/edit/delete nodes and edges
- Edit top-level variables and scoring
- Validate (strict or draft)
- Evaluate current in-memory scenario
- Render SVG preview
- Status panel for errors/warnings/draft warnings/skipped items

UI structure:

- Left: variables, nodes, edges lists + quick-add buttons
- Main: selected item form editor
- Top: load/save/validate/evaluate/render actions
- Right: status + preview

Authoring helpers:

- Auto-generate IDs from labels
- Duplicate node/edge
- Search/filter nodes/edges
- Mark guessed/incomplete/complete flags

## Scenario model (JSON)

Top-level:

- `scenario_name`, `description`, `variables`, `scoring`, `nodes`, `edges`
- Optional: `mode`, `metadata`, `editor`

Edge semantics:

- `branch`: independent/coexisting consequences in same scope
- `fork`: mutually exclusive alternatives per simulated path
- `escalate`: risk/pressure worsens
- `resolve`: de-escalation/closure

Probability interpretation:

- Fork siblings should typically sum near 1.0 (validator warns if not).
- Branch edges are independent and need not sum to 1.0.

Loop controls:

- `max_depth=12`
- `max_visits_per_node=2`
- `probability_cutoff=0.01`

## Scoring

Lower is better:

```text
composite_score =
  catastrophic_weight * catastrophic_probability
  - positive_weight * positive_end_probability
  + harm_weight * expected_harm
  + uncertainty_weight * expected_uncertainty_penalty
  + reversibility_weight * expected_reversibility_penalty
```

## Rendering behavior in draft mode

- Complete edges render normally.
- Incomplete edges with known endpoints render as dashed placeholders.
- Incomplete edges missing endpoints are omitted.

## Example files

- `scenarios/example_scenario.json`
- `scenarios/example_parallel_fork_scenario.json`
- `scenarios/draft_example.json` (contains guessed + incomplete content intentionally)

## Example authoring workflow

1. `python main.py new-draft scenarios/my_draft.json --open-editor`
2. Add a few decision nodes and rough edges.
3. Save draft repeatedly while ideas are incomplete.
4. Use draft validate to inspect warnings.
5. Fill missing edge fields and set draft status to complete.
6. Run strict validate/evaluate/render/report once modeling is complete.

## Run updated editor on macOS

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python main.py edit scenarios/draft_example.json`
5. In browser, click **Save Draft**
6. `python main.py validate scenarios/draft_example.json --mode draft`
7. `python main.py evaluate scenarios/draft_example.json`
8. `python main.py render scenarios/draft_example.json --format svg`
