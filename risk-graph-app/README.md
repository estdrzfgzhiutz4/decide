# risk-graph-app

CLI-first local Python app for modeling and comparing branching decision futures with strong catastrophic-risk avoidance.

## Purpose

`risk-graph-app` evaluates **starting decisions** across the full reachable future graph (not greedily one step at a time). It supports:

- Coexisting branches in the same scope.
- Hard fork alternatives that are mutually exclusive **within a single path** but remain visible globally for planning.
- State-variable dependencies via conditions and effects.
- Escalation chains, resolve transitions, and bounded loops.
- Top-3 safest decision ranking with explicit downstream impact metrics.

No LLMs, no network services, no database, no GUI framework.

## Requirements

- macOS
- Python 3.11+
- Graphviz binary installed locally (e.g., `brew install graphviz`)
- Python dependency: `graphviz`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI usage

```bash
python main.py validate scenarios/example_scenario.json
python main.py evaluate scenarios/example_scenario.json
python main.py render scenarios/example_scenario.json --format svg
python main.py render scenarios/example_scenario.json --format png
python main.py report scenarios/example_scenario.json
```

Render output goes into `output/`. Report output is `output/report.txt`.

## Scenario JSON structure

Top-level fields:

- `scenario_name` (string)
- `description` (string)
- `variables` (object of primitive values)
- `scoring` with:
  - `catastrophic_weight`
  - `positive_weight`
  - `harm_weight`
  - `uncertainty_weight`
  - `reversibility_weight`
- `nodes` array
- `edges` array

### Nodes

Fields:

- `id` (unique string)
- `label` (string)
- `type` in `decision,event,actor,outcome,terminal_positive,terminal_failure`
- `harm` (number, default `0`)
- `terminal` (boolean)
- `positive` (boolean)
- `failure` (boolean)
- `notes` (optional)
- `tags` (optional list)

### Edges

Fields:

- `id` (unique string)
- `from` / `to` (node ids)
- `probability` (0..1)
- `transition_kind` in `branch,fork,escalate,resolve`
- `active_if` (optional condition list)
- `effects` (optional state mutations)
- `uncertainty` (0..1, default `0`)
- `reversibility_cost` (number, default `0`)
- `notes` (optional)

### Condition ops

- `equals`, `not_equals`, `is_true`, `is_false`
- `greater_than`, `greater_or_equal`, `less_than`, `less_or_equal`

### Effect ops

- `set`, `increment`, `decrement`

## Transition semantics

- **branch**: independent/coexisting consequences in same scope (handled as independent probabilistic events).
- **fork**: exclusive alternatives per simulated path; sibling fork branches remain visible in scenario/reporting.
- **escalate**: worsens pressure/risk chain.
- **resolve**: de-escalates or safely closes chain.

## Fork probabilities vs branch probabilities

V1 intentionally treats probability mass differently:

- Fork siblings from same source should usually sum near 1.0 (validator warns if not).
- Branch edges may be independent and are **not required** to sum to 1.0.

## Loops and staged escalation

The engine supports bounded loops with safeguards:

- `max_depth` (default `12`)
- `max_visits_per_node` (default `2`)
- `probability_cutoff` (default `0.01`)

Many real-world repeated patterns are better modeled as staged escalation nodes instead of literal cycles.

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

Catastrophic risk is designed to dominate ranking.

## Validation behavior

Validator catches:

- duplicate node/edge IDs
- missing node references
- invalid ranges/types/ops
- terminal nodes with outgoing edges
- decision nodes with no outgoing edges
- unknown variables in conditions
- unknown variables in effects (**rejected in V1** to prevent typo-induced silent variable creation)

Unreachable nodes are warnings.

## Example output summary (evaluate)

- Ranked decisions safest-first
- Catastrophic probability
- Positive-end probability
- Expected harm
- Composite score

`report` additionally includes:

- top-3 safest starting decisions
- top dangerous paths (up to 5)
- top positive paths
- back-propagated interpretation sentence per decision
- validation warnings and unreachable nodes

## Run on macOS

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python main.py validate scenarios/example_scenario.json`
5. `python main.py evaluate scenarios/example_scenario.json`
6. `python main.py render scenarios/example_scenario.json --format svg`
7. `python main.py report scenarios/example_scenario.json`
