import json
import tempfile
import unittest
from pathlib import Path

from meme_studio.commands import build_conf_schema, load_generated_commands


class GeneratedMemeCommandsTest(unittest.TestCase):
    def test_load_generated_commands_converts_manifest_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write_generated_commands(Path(tmp))

            commands = load_generated_commands(config_path)

            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0].name, "测试生成")
            self.assertEqual(commands[0].script, "render_manifest_template.py")
            self.assertEqual(commands[0].output_ext, "gif")
            self.assertEqual(commands[0].message, "测试生成中...")
            self.assertEqual(commands[0].extra_args, ("data/测试生成/manifest.json",))

    def test_build_conf_schema_can_include_generated_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write_generated_commands(Path(tmp))

            schema = build_conf_schema(generated_path=config_path)

            self.assertIn("测试生成", schema)
            self.assertEqual(schema["测试生成"]["default"], True)

    def _write_generated_commands(self, root: Path) -> Path:
        config_path = root / "generated_meme_commands.json"
        config_path.write_text(
            json.dumps(
                {
                    "commands": [
                        {
                            "name": "测试生成",
                            "manifest": "data/测试生成/manifest.json",
                            "output": "gif",
                            "message": "测试生成中...",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return config_path


if __name__ == "__main__":
    unittest.main()
