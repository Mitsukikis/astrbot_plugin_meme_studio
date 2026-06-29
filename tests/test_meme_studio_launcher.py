import tempfile
import unittest
from pathlib import Path

from meme_studio_launcher import find_project_root


class MemeStudioLauncherTest(unittest.TestCase):
    def test_find_project_root_walks_up_from_dist_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "metadata.yaml").write_text('name: "表情包制造厂"\n', encoding="utf-8")
            (root / "meme_commands.py").write_text("# marker\n", encoding="utf-8")
            dist = root / "dist"
            dist.mkdir()

            self.assertEqual(find_project_root(dist), root)


if __name__ == "__main__":
    unittest.main()
