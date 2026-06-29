import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "_conf_schema.json"


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meme_studio.commands import build_conf_schema  # noqa: E402


def main() -> None:
    schema = build_conf_schema()
    SCHEMA_PATH.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("updated {}".format(SCHEMA_PATH))


if __name__ == "__main__":
    main()
