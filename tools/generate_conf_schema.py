import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "_conf_schema.json"


def _load_build_conf_schema():
    module_path = ROOT / "meme_commands.py"
    spec = importlib.util.spec_from_file_location("meme_commands", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 meme_commands.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_conf_schema


def main() -> None:
    build_conf_schema = _load_build_conf_schema()
    schema = build_conf_schema()
    SCHEMA_PATH.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("updated {}".format(SCHEMA_PATH))


if __name__ == "__main__":
    main()
