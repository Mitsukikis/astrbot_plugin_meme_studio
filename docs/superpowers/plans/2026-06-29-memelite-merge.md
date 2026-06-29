# Meme Generator Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional `meme-generator` engine to Meme Studio while preserving the existing local visual-template engine.

**Architecture:** Keep `main.py` and the local template runtime thin. Add `generator_engine.py`, `generator_params.py`, and `generator_runtime.py` under `meme_studio/`, then wire them into `meme_studio/runtime.py` after local command matching. The new engine is lazy, optional, configurable, and tested with fakes so local development does not require the external package.

**Tech Stack:** Python 3.8+, AstrBot plugin API, optional `meme_generator~=0.2.0`, Pillow, `httpx`, `unittest`.

---

## File Structure

Create:

```text
meme_studio/generator_engine.py
meme_studio/generator_params.py
meme_studio/generator_runtime.py
tests/test_generator_engine.py
tests/test_generator_runtime.py
tests/test_generator_params.py
```

Modify:

```text
meme_studio/runtime.py
requirements.txt
_conf_schema.json
README.md
SECURITY_REVIEW.md
```

---

### Task 1: Generator Engine Adapter

**Files:**
- Create: `meme_studio/generator_engine.py`
- Test: `tests/test_generator_engine.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_generator_engine.py` with tests for missing dependency, exact/fuzzy matching, bytes unwrapping, and disabled keyword behavior:

```python
import io
import unittest

from meme_studio.generator_engine import GeneratorEngine, GeneratorParams


class FakeInfo:
    keywords = ["摸", "摸摸"]
    tags = ["action"]
    params = GeneratorParams(min_images=1, max_images=1, min_texts=0, max_texts=1, default_texts=[])


class FakeMeme:
    key = "petpet"
    info = FakeInfo()

    def generate_preview(self):
        return io.BytesIO(b"preview")

    def generate(self, images, texts, options):
        return b"generated"


class GeneratorEngineTest(unittest.TestCase):
    def test_missing_dependency_is_not_available(self):
        engine = GeneratorEngine(importer=lambda: (_ for _ in ()).throw(ImportError("missing")))
        self.assertFalse(engine.available)
        self.assertEqual(engine.match_keyword("摸 @someone", fuzzy=False, disabled=[]), None)

    def test_match_keyword_exact_and_fuzzy(self):
        engine = GeneratorEngine(importer=lambda: [FakeMeme()])
        self.assertEqual(engine.match_keyword("摸 @someone", fuzzy=False, disabled=[]), "摸")
        self.assertIsNone(engine.match_keyword("请你摸一下", fuzzy=False, disabled=[]))
        self.assertEqual(engine.match_keyword("请你摸一下", fuzzy=True, disabled=[]), "摸")

    def test_disabled_keyword_is_ignored(self):
        engine = GeneratorEngine(importer=lambda: [FakeMeme()])
        self.assertIsNone(engine.match_keyword("摸", fuzzy=False, disabled=["摸"]))

    def test_info_and_preview_unwrap_bytesio(self):
        engine = GeneratorEngine(importer=lambda: [FakeMeme()])
        info, preview = engine.get_meme_info("摸")
        self.assertIn("petpet", info)
        self.assertEqual(preview, b"preview")
```

- [ ] **Step 2: Run tests to verify red**

Run:

```powershell
python -B -m unittest tests.test_generator_engine -v
```

Expected: import error because `meme_studio.generator_engine` does not exist.

- [ ] **Step 3: Implement engine**

Implement a lazy adapter:

```python
import asyncio
import io
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Any, Callable, Iterable, Optional

from astrbot.api import logger


@dataclass(frozen=True)
class GeneratorParams:
    min_images: int = 0
    max_images: int = 0
    min_texts: int = 0
    max_texts: int = 0
    default_texts: list[str] = field(default_factory=list)


class GeneratorEngine:
    def __init__(self, importer: Optional[Callable[[], Iterable[Any]]] = None):
        self._importer = importer or self._load_from_meme_generator
        self._memes: list[Any] = []
        self._load_error: Optional[str] = None
        self._loaded = False

    @property
    def available(self) -> bool:
        self._ensure_loaded()
        return bool(self._memes)

    @property
    def load_error(self) -> Optional[str]:
        self._ensure_loaded()
        return self._load_error

    def _load_from_meme_generator(self) -> Iterable[Any]:
        from meme_generator import get_memes
        return get_memes()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            self._memes = list(self._importer())
        except Exception as exc:
            self._load_error = str(exc)
            self._memes = []
            logger.warning("meme-generator unavailable: %s", exc)

    def _keywords(self, meme: Any) -> list[str]:
        info = getattr(meme, "info", None)
        if info is not None and hasattr(info, "keywords"):
            return list(info.keywords)
        return list(getattr(meme, "keywords", []))

    def _params(self, meme: Any) -> GeneratorParams:
        info = getattr(meme, "info", None)
        raw = getattr(info, "params", None) if info is not None else getattr(meme, "params_type", None)
        if raw is None:
            return GeneratorParams()
        return GeneratorParams(
            min_images=int(getattr(raw, "min_images", 0)),
            max_images=int(getattr(raw, "max_images", 0)),
            min_texts=int(getattr(raw, "min_texts", 0)),
            max_texts=int(getattr(raw, "max_texts", 0)),
            default_texts=list(getattr(raw, "default_texts", []) or []),
        )

    def find_meme(self, keyword: str) -> Any | None:
        self._ensure_loaded()
        for meme in self._memes:
            if keyword == getattr(meme, "key", "") or keyword in self._keywords(meme):
                return meme
        return None

    def match_keyword(self, text: str, fuzzy: bool, disabled: list[str]) -> str | None:
        self._ensure_loaded()
        if not text:
            return None
        candidates = [keyword for meme in self._memes for keyword in self._keywords(meme)]
        candidates = [keyword for keyword in candidates if keyword not in disabled]
        if fuzzy:
            return next((keyword for keyword in candidates if keyword and keyword in text), None)
        first_word = text.split(maxsplit=1)[0]
        return next((keyword for keyword in candidates if keyword == first_word), None)

    @staticmethod
    def unwrap_bytes(result: Any, action: str) -> bytes:
        if isinstance(result, io.BytesIO):
            return result.getvalue()
        if isinstance(result, (bytes, bytearray, memoryview)):
            return bytes(result)
        detail = getattr(result, "feedback", None) or getattr(result, "error", None) or repr(result)
        raise RuntimeError(f"{action} failed: {detail}")

    def get_meme_info(self, keyword: str) -> tuple[str, bytes] | None:
        meme = self.find_meme(keyword)
        if meme is None:
            return None
        params = self._params(meme)
        keywords = self._keywords(meme)
        tags = list(getattr(getattr(meme, "info", None), "tags", getattr(meme, "tags", [])) or [])
        lines = [f"Name: {getattr(meme, 'key', keyword)}", f"Keywords: {keywords}"]
        if params.max_images:
            lines.append(f"Images: {params.min_images}-{params.max_images}")
        if params.max_texts:
            lines.append(f"Texts: {params.min_texts}-{params.max_texts}")
        if tags:
            lines.append(f"Tags: {tags}")
        preview = self.unwrap_bytes(meme.generate_preview(), f"generate preview for {keyword}")
        return "\n".join(lines), preview

    async def generate(self, keyword: str, images: list[tuple[str, bytes]], texts: list[str], options: dict[str, object]) -> bytes | None:
        meme = self.find_meme(keyword)
        if meme is None:
            return None
        result = await asyncio.to_thread(meme.generate, [data for _, data in images], texts, options)
        return self.unwrap_bytes(result, f"generate meme {keyword}")
```

- [ ] **Step 4: Run engine tests**

Run:

```powershell
python -B -m unittest tests.test_generator_engine -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add meme_studio/generator_engine.py tests/test_generator_engine.py
git commit -m "feat: add optional meme generator engine"
```

---

### Task 2: Parameter Collector

**Files:**
- Create: `meme_studio/generator_params.py`
- Test: `tests/test_generator_params.py`

- [ ] **Step 1: Write failing tests**

Create tests that use fake events and a fake loader:

```python
import unittest

from meme_studio.generator_engine import GeneratorParams
from meme_studio.generator_params import collect_generator_params


class FakeEvent:
    message_str = "/摸 hello mood=happy"

    def get_sender_id(self):
        return "10001"

    def get_self_id(self):
        return "20002"

    def get_sender_name(self):
        return "sender"


class GeneratorParamsCollectorTest(unittest.IsolatedAsyncioTestCase):
    async def test_collects_text_options_and_sender_avatar_fallback(self):
        async def avatar_loader(qq):
            return f"avatar-{qq}".encode()

        images, texts, options = await collect_generator_params(
            FakeEvent(),
            GeneratorParams(min_images=1, max_images=1, min_texts=1, max_texts=2, default_texts=[]),
            command_text="摸 hello mood=happy",
            avatar_loader=avatar_loader,
        )

        self.assertEqual(images, [("sender", b"avatar-10001")])
        self.assertEqual(texts, ["hello"])
        self.assertEqual(options, {"mood": "happy"})
```

- [ ] **Step 2: Verify red**

Run:

```powershell
python -B -m unittest tests.test_generator_params -v
```

Expected: import error because `generator_params.py` does not exist.

- [ ] **Step 3: Implement collector**

Implement `collect_generator_params(event, params, command_text, avatar_loader)` with duck-typed AstrBot components. It should parse tokens after the first command word, split `key=value` into options, keep plain tokens as texts, add sender avatar fallback when `min_images` requires one, and clip to max counts.

- [ ] **Step 4: Verify green**

Run:

```powershell
python -B -m unittest tests.test_generator_params -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add meme_studio/generator_params.py tests/test_generator_params.py
git commit -m "feat: collect meme generator parameters"
```

---

### Task 3: Runtime Integration

**Files:**
- Create: `meme_studio/generator_runtime.py`
- Modify: `meme_studio/runtime.py`
- Test: `tests/test_generator_runtime.py`

- [ ] **Step 1: Write failing tests**

Create tests for trigger policy and local priority:

```python
import unittest

from meme_studio.generator_runtime import GeneratorRuntimeConfig, MemeGeneratorRuntime
from meme_studio.runtime import MemeStudioRuntime


class FakeEngine:
    def __init__(self):
        self.generated = []

    def match_keyword(self, text, fuzzy, disabled):
        return "摸" if text.startswith("摸") else None


class GeneratorRuntimeTest(unittest.TestCase):
    def test_strips_slash_prefix_when_prefix_required(self):
        runtime = MemeGeneratorRuntime(FakeEngine(), GeneratorRuntimeConfig())
        self.assertEqual(runtime.extract_command_text("/摸 @10001", is_wake=False), "摸 @10001")

    def test_ignores_plain_message_when_prefix_required(self):
        runtime = MemeGeneratorRuntime(FakeEngine(), GeneratorRuntimeConfig(generator_need_prefix=True))
        self.assertIsNone(runtime.extract_command_text("摸 @10001", is_wake=False))

    def test_local_command_match_remains_available(self):
        self.assertTrue(MemeStudioRuntime._has_command_boundary("摸 @10001", "摸"))
```

- [ ] **Step 2: Verify red**

Run:

```powershell
python -B -m unittest tests.test_generator_runtime -v
```

Expected: import error because `generator_runtime.py` does not exist.

- [ ] **Step 3: Implement runtime layer**

Add:

- `GeneratorRuntimeConfig.from_mapping(config)`.
- `MemeGeneratorRuntime.extract_command_text(message, is_wake)`.
- `MemeGeneratorRuntime.handle(event, image_loader)` async generator.
- Help/detail/blacklist command helpers.

Wire in `MemeStudioRuntime.__init__`:

```python
from .generator_engine import GeneratorEngine
from .generator_runtime import GeneratorRuntimeConfig, MemeGeneratorRuntime

self.generator_runtime = MemeGeneratorRuntime(
    GeneratorEngine(),
    GeneratorRuntimeConfig.from_mapping(self.config),
)
```

Wire in `on_message` after local command handling returns no command:

```python
async for result in self.generator_runtime.handle(event, self._read_image_source_bytes):
    yield result
```

Add `_read_image_source_bytes(source: str) -> bytes` using the existing validated download/local/base64 code path with byte limits.

- [ ] **Step 4: Verify runtime tests**

Run:

```powershell
python -B -m unittest tests.test_generator_runtime -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add meme_studio/generator_runtime.py meme_studio/runtime.py tests/test_generator_runtime.py
git commit -m "feat: integrate meme generator runtime"
```

---

### Task 4: Config, Requirements, Docs

**Files:**
- Modify: `requirements.txt`
- Modify: `_conf_schema.json`
- Modify: `README.md`
- Modify: `SECURITY_REVIEW.md`

- [ ] **Step 1: Add dependency**

Add:

```text
meme_generator~=0.2.0
```

- [ ] **Step 2: Add config schema keys**

Add keys from the design: `generator_enabled`, `generator_need_prefix`, `generator_extra_prefix`, `generator_fuzzy_match`, `generator_check_resources`, `generator_timeout_seconds`, `generator_compress_static`, `generator_disabled_list`.

- [ ] **Step 3: Document operation**

README must include:

- local templates have priority;
- `/meme帮助` and `/meme详情 <keyword>`;
- Linux/Docker system dependency note;
- how to disable `generator_enabled`;
- note that memelite was used only as an architectural reference because of license differences.

- [ ] **Step 4: Verify docs and schema**

Run:

```powershell
python -B -m unittest discover -v
python -m json.tool _conf_schema.json > $null
```

Expected: tests pass and schema is valid JSON.

- [ ] **Step 5: Commit**

```powershell
git add requirements.txt _conf_schema.json README.md SECURITY_REVIEW.md
git commit -m "docs: document meme generator integration"
```

---

### Task 5: Review And Full Verification

**Files:**
- All changed files

- [ ] **Step 1: Run full verification**

```powershell
python -B -m unittest discover -v
python -m compileall -q .
node --check meme_studio/web/app.js
git diff --check
git status --short --untracked-files=all
```

- [ ] **Step 2: Check no external source copied**

Run:

```powershell
Select-String -Path 'meme_studio/*.py' -Pattern 'Zhalslar|astrbot_plugin_memelite|AGPL' -SimpleMatch
```

Expected: no matches in implementation files. Documentation may mention the reference plugin.

- [ ] **Step 3: Commit any verification fixes**

If verification finds issues, fix them with tests first and commit with a focused message.

---

## Self-Review

- Spec coverage: engine, params, runtime, config, docs, and verification tasks cover all design requirements.
- Placeholder scan: no unresolved placeholder steps remain.
- Type consistency: `GeneratorEngine`, `GeneratorParams`, `GeneratorRuntimeConfig`, and `MemeGeneratorRuntime` are consistently named across tasks.
