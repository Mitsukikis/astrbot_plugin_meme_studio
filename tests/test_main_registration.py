import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FakeLogger:
    def warning(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass


class FakeFilter:
    registered_commands = {}

    class EventMessageType:
        ALL = "all"

    @staticmethod
    def command(name):
        def decorate(func):
            full_name = "{}_{}".format(func.__module__, func.__name__)
            entry = FakeFilter.registered_commands.setdefault(
                full_name,
                {
                    "handler_name": func.__name__,
                    "commands": [],
                },
            )
            entry["commands"].append(name)
            func.__astrbot_handler_full_name__ = full_name
            func.__astrbot_command_name__ = name
            return func

        return decorate

    @staticmethod
    def event_message_type(message_type):
        def decorate(func):
            func.__astrbot_event_message_type__ = message_type
            return func

        return decorate


class FakeStar:
    def __init__(self, context):
        self.context = context


class FakeContext:
    pass


class FakeAstrMessageEvent:
    pass


class FakeAt:
    def __init__(self, qq):
        self.qq = qq


class FakeImage:
    def __init__(self, url=None, file=None):
        self.url = url
        self.file = file

    @classmethod
    def fromBytes(cls, image_bytes):
        return cls(file=image_bytes)


class MainRegistrationTest(unittest.TestCase):
    def setUp(self):
        self._old_modules = {}
        for name in self._astrbot_module_names():
            self._old_modules[name] = sys.modules.get(name)

        sys.path.insert(0, str(ROOT))
        self._install_astrbot_stubs()
        sys.modules.pop("main", None)
        sys.modules.pop("meme_studio.runtime", None)

    def tearDown(self):
        sys.modules.pop("main", None)
        sys.modules.pop("meme_studio.runtime", None)
        if sys.path and sys.path[0] == str(ROOT):
            sys.path.pop(0)

        for name, module in self._old_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_dispatch_handler_is_registered_inside_plugin_class(self):
        main = importlib.import_module("main")

        self.assertEqual(
            main.MemeArsenal.on_message.__astrbot_event_message_type__,
            FakeFilter.EventMessageType.ALL,
        )

    def test_main_uses_runtime_plugin_class(self):
        import main
        from meme_studio.runtime import MemeStudioRuntime

        self.assertIs(main.MemeStudioRuntime, MemeStudioRuntime)

    def test_builtin_commands_are_registered_as_astrbot_commands(self):
        main = importlib.import_module("main")

        self.assertIn("撅", self._registered_command_names(main))

    def test_generated_commands_are_registered_as_astrbot_commands(self):
        meme_commands = importlib.import_module("meme_studio.commands")
        old_generated_path = meme_commands.GENERATED_COMMANDS_PATH

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "generated_meme_commands.json"
            config_path.write_text(
                json.dumps(
                    {
                        "commands": [
                            {
                                "name": "刚刚新增模板",
                                "manifest": "data/刚刚新增模板/manifest.json",
                                "output": "png",
                                "message": "正在生成...",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            try:
                meme_commands.GENERATED_COMMANDS_PATH = config_path
                sys.modules.pop("main", None)
                main = importlib.import_module("main")

                self.assertIn("刚刚新增模板", self._registered_command_names(main))
            finally:
                meme_commands.GENERATED_COMMANDS_PATH = old_generated_path
                sys.modules.pop("main", None)

    def test_astrbot_command_handlers_have_unique_registry_entries(self):
        main = importlib.import_module("main")
        meme_commands = importlib.import_module("meme_studio.commands")
        command_entries = [
            entry
            for entry in FakeFilter.registered_commands.values()
            if entry["commands"]
        ]
        command_names = {
            name
            for entry in command_entries
            for name in entry["commands"]
        }
        expected_commands = {command.name for command in meme_commands.all_meme_commands()}

        self.assertEqual(command_names, expected_commands)
        self.assertEqual(len(command_entries), len(expected_commands))

    def test_dispatcher_matches_registry_command(self):
        main = importlib.import_module("main")
        plugin = main.MemeArsenal(FakeContext(), {})
        event = types.SimpleNamespace(
            message_str="/砸 @someone",
            message_obj=types.SimpleNamespace(message_str="/砸 @someone", message=[]),
        )

        self.assertEqual(plugin._match_command(event).name, "砸")

    def test_dispatcher_matches_command_when_at_has_no_spacing(self):
        main = importlib.import_module("main")
        plugin = main.MemeArsenal(FakeContext(), {})
        event = types.SimpleNamespace(
            message_str="/砸@someone",
            message_obj=types.SimpleNamespace(message_str="/砸@someone", message=[]),
        )

        self.assertEqual(plugin._match_command(event).name, "砸")

    def test_dispatcher_reads_generated_commands_when_matching(self):
        main = importlib.import_module("main")
        meme_commands = importlib.import_module("meme_studio.commands")
        old_generated_path = meme_commands.GENERATED_COMMANDS_PATH

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "generated_meme_commands.json"
            config_path.write_text(
                json.dumps(
                    {
                        "commands": [
                            {
                                "name": "刚刚新增模板",
                                "manifest": "data/刚刚新增模板/manifest.json",
                                "output": "png",
                                "message": "正在生成...",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            try:
                meme_commands.GENERATED_COMMANDS_PATH = config_path
                plugin = main.MemeArsenal(FakeContext(), {})
                event = types.SimpleNamespace(
                    message_str="/刚刚新增模板 @someone",
                    message_obj=types.SimpleNamespace(
                        message_str="/刚刚新增模板 @someone",
                        message=[],
                    ),
                )

                command = plugin._match_command(event)

                self.assertIsNotNone(command)
                self.assertEqual(command.name, "刚刚新增模板")
            finally:
                meme_commands.GENERATED_COMMANDS_PATH = old_generated_path

    def test_remote_image_url_rejects_private_hosts(self):
        main = importlib.import_module("main")
        plugin = main.MemeArsenal(FakeContext(), {})

        with self.assertRaises(ValueError):
            plugin._validate_remote_image_url("http://127.0.0.1/private.png")

        with self.assertRaises(ValueError):
            plugin._validate_remote_image_url("http://10.0.0.1/private.png")

    def test_remote_image_url_accepts_public_http_hosts(self):
        main = importlib.import_module("main")
        plugin = main.MemeArsenal(FakeContext(), {})

        plugin._validate_remote_image_url("https://1.1.1.1/avatar.png")

    @staticmethod
    def _registered_command_names(main):
        return {
            getattr(member, "__astrbot_command_name__", None)
            for member in vars(main.MemeArsenal).values()
            if getattr(member, "__astrbot_command_name__", None)
        }

    def _install_astrbot_stubs(self):
        FakeFilter.registered_commands = {}

        astrbot = types.ModuleType("astrbot")
        api = types.ModuleType("astrbot.api")
        api.logger = FakeLogger()

        event = types.ModuleType("astrbot.api.event")
        event.AstrMessageEvent = FakeAstrMessageEvent
        event.filter = FakeFilter

        message_components = types.ModuleType("astrbot.api.message_components")
        message_components.At = FakeAt
        message_components.Image = FakeImage

        star = types.ModuleType("astrbot.api.star")
        star.Context = FakeContext
        star.Star = FakeStar

        sys.modules["astrbot"] = astrbot
        sys.modules["astrbot.api"] = api
        sys.modules["astrbot.api.event"] = event
        sys.modules["astrbot.api.message_components"] = message_components
        sys.modules["astrbot.api.star"] = star

    @staticmethod
    def _astrbot_module_names():
        return (
            "astrbot",
            "astrbot.api",
            "astrbot.api.event",
            "astrbot.api.message_components",
            "astrbot.api.star",
        )


if __name__ == "__main__":
    unittest.main()
