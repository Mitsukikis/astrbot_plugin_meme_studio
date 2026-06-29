import json
import tempfile
import unittest
from pathlib import Path

from meme_commands import MEME_COMMANDS, build_conf_schema, load_generated_commands


ROOT = Path(__file__).resolve().parents[1]


class MemeCommandRegistryTest(unittest.TestCase):
    def test_command_names_are_unique(self):
        names = [command.name for command in MEME_COMMANDS]

        self.assertEqual(len(names), len(set(names)))

    def test_every_command_script_exists(self):
        missing = [
            command.script
            for command in MEME_COMMANDS
            if not (ROOT / "scripts" / command.script).is_file()
        ]

        self.assertEqual(missing, [])

    def test_conf_schema_matches_registry(self):
        schema_path = ROOT / "_conf_schema.json"
        actual_schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(actual_schema, build_conf_schema())

    def test_generated_commands_reject_unsafe_manifest_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "generated_meme_commands.json"
            config_path.write_text(
                json.dumps(
                    {
                        "commands": [
                            {
                                "name": "安全模板",
                                "manifest": "data/安全模板/manifest.json",
                                "output": "gif",
                            },
                            {
                                "name": "穿越模板",
                                "manifest": "../outside/manifest.json",
                                "output": "gif",
                            },
                            {
                                "name": "绝对路径模板",
                                "manifest": "C:/Windows/win.ini",
                                "output": "png",
                            },
                            {
                                "name": "../坏名字",
                                "manifest": "data/坏名字/manifest.json",
                                "output": "png",
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            commands = load_generated_commands(config_path)

        self.assertEqual([command.name for command in commands], ["安全模板"])
        self.assertEqual(commands[0].extra_args, ("data/安全模板/manifest.json",))


if __name__ == "__main__":
    unittest.main()
