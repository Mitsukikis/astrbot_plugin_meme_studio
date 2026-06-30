import zipfile
import unittest

from tools import package_plugin_zip


ROOT = package_plugin_zip.ROOT
PACKAGE_NAME = package_plugin_zip.PACKAGE_NAME


class PackagePluginZipTest(unittest.TestCase):
    def test_archive_name_prefixes_package_directory(self):
        self.assertEqual(
            package_plugin_zip.archive_name(ROOT / "main.py"),
            f"{PACKAGE_NAME}/main.py",
        )

    def test_archive_name_uses_forward_slashes(self):
        name = package_plugin_zip.archive_name(ROOT / "meme_studio" / "web" / "index.html")

        self.assertEqual(name, f"{PACKAGE_NAME}/meme_studio/web/index.html")
        self.assertNotIn("\\", name)

    def test_should_exclude_local_and_build_artifacts(self):
        excluded_paths = [
            ROOT / "MemeStudio.exe",
            ROOT / "tests" / "test_package_plugin_zip.py",
            ROOT / ".meme_studio_sessions" / "session.json",
            ROOT / "build" / "artifact.txt",
            ROOT / "dist" / "artifact.txt",
            ROOT / "docs" / "notes.md",
            ROOT / "__pycache__" / "main.cpython-312.pyc",
            ROOT / ".git" / "config",
            ROOT / "MemeStudio.spec",
            ROOT / "main.cpython-312.pyc",
        ]

        for path in excluded_paths:
            with self.subTest(path=path):
                self.assertFalse(package_plugin_zip.should_include(path))

    def test_main_creates_zip_with_package_root_and_excludes_artifacts(self):
        package_plugin_zip.main()

        try:
            self.assertTrue(package_plugin_zip.OUTPUT.exists())
            with zipfile.ZipFile(package_plugin_zip.OUTPUT) as archive:
                names = archive.namelist()

            self.assertIn(f"{PACKAGE_NAME}/main.py", names)
            for name in names:
                with self.subTest(name=name):
                    self.assertNotIn("\\", name)
                    self.assertNotIn(f"{PACKAGE_NAME}/tests/", name)
                    self.assertNotIn(f"{PACKAGE_NAME}/docs/", name)
                    self.assertNotIn(f"{PACKAGE_NAME}/.git/", name)
                    self.assertNotIn("__pycache__/", name)
                    self.assertFalse(name.endswith(".gitignore"))
                    self.assertFalse(name.endswith(".exe"))
                    self.assertFalse(name.endswith(".pyc"))
                    self.assertFalse(name.endswith(".spec"))
        finally:
            package_plugin_zip.OUTPUT.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
