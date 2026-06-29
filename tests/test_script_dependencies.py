import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScriptDependencyTest(unittest.TestCase):
    def test_scripts_do_not_import_removed_meme_generator_utils(self):
        offenders = []
        for script_path in (ROOT / "scripts").glob("*.py"):
            content = script_path.read_text(encoding="utf-8")
            if "meme_generator.utils" in content:
                offenders.append(script_path.name)

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
