import json
from pathlib import Path

from app.editor_server import EditorService
from app.loader import load_scenario


def test_editor_service_save_load_endpoints_logic(tmp_path: Path) -> None:
    src = Path("scenarios/draft_example.json")
    target = tmp_path / "draft.json"
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    service = EditorService(scenario_path=target, preview_path=tmp_path / "preview.svg")
    scenario = service.get_scenario()
    assert scenario["scenario_name"] == "draft_example"

    scenario["description"] = "updated"
    out = service.save(scenario, mode="draft")
    assert out["ok"] is True

    loaded = load_scenario(target)
    assert loaded.description == "updated"


def test_new_draft_command_creates_valid_skeleton(tmp_path: Path) -> None:
    from app.cli import main

    draft_path = tmp_path / "new_draft.json"
    code = main(["new-draft", str(draft_path)])
    assert code == 0
    data = json.loads(draft_path.read_text(encoding="utf-8"))
    assert data["mode"] == "draft"
    assert data["nodes"] == []
