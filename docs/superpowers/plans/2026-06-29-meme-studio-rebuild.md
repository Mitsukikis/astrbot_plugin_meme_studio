# Meme Studio Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the current plugin into `astrbot_plugin_meme_studio`, a review-ready AstrBot plugin with a separated bot runtime and a token-protected browser studio for Linux server use.

**Architecture:** Keep one AstrBot plugin, but split responsibilities into a focused `meme_studio/` package. `main.py` becomes the thin AstrBot adapter, runtime generation lives in `meme_studio/runtime.py`, template rendering lives in `meme_studio/renderer.py`, and the browser console lives in `meme_studio/studio_service.py`, `meme_studio/studio_server.py`, and `meme_studio/studio_security.py`.

**Tech Stack:** Python 3.8+, AstrBot plugin API, `httpx`, Pillow, OpenCV, `unittest`, `http.server`, vanilla HTML/CSS/JavaScript.

---

## File Structure

Implementation starts from:

```text
C:\Users\35559\Documents\Codex\2026-06-04\f-astrbot-plugin-meme-manufacturer-astrbot\publish\astrbot_plugin_meme_manufacturer
```

New working project root:

```text
C:\Users\35559\Documents\Codex\2026-06-04\f-astrbot-plugin-meme-manufacturer-astrbot\publish\astrbot_plugin_meme_studio
```

Final structure:

```text
astrbot_plugin_meme_studio/
├─ main.py
├─ meme_studio/
│  ├─ __init__.py
│  ├─ commands.py
│  ├─ runtime.py
│  ├─ renderer.py
│  ├─ studio_security.py
│  ├─ studio_service.py
│  ├─ studio_server.py
│  └─ web/
│     ├─ app.js
│     ├─ index.html
│     └─ styles.css
├─ tools/
│  ├─ build_meme_studio_exe.py
│  ├─ generate_conf_schema.py
│  ├─ meme_studio.py
│  └─ package_plugin_zip.py
├─ data/
├─ scripts/
├─ tests/
├─ metadata.yaml
├─ README.md
├─ SECURITY_REVIEW.md
├─ requirements.txt
├─ generated_meme_commands.json
└─ _conf_schema.json
```

---

### Task 1: Create New Project Root And Rename Identity

**Files:**
- Create directory: `C:\Users\35559\Documents\Codex\2026-06-04\f-astrbot-plugin-meme-manufacturer-astrbot\publish\astrbot_plugin_meme_studio`
- Modify: `metadata.yaml`
- Modify: `README.md`
- Modify: `SECURITY_REVIEW.md`
- Modify: `tools/package_plugin_zip.py`

- [ ] **Step 1: Copy the clean source into the new root**

Run from `C:\Users\35559\Documents\Codex\2026-06-04\f-astrbot-plugin-meme-manufacturer-astrbot\publish`:

```powershell
$source = Resolve-Path -LiteralPath '.\astrbot_plugin_meme_manufacturer'
$target = Join-Path (Get-Location) 'astrbot_plugin_meme_studio'
if (Test-Path -LiteralPath $target) {
  throw "Target already exists: $target"
}
Copy-Item -LiteralPath $source -Destination $target -Recurse
Remove-Item -LiteralPath (Join-Path $target '.git') -Recurse -Force
```

Expected: a new `astrbot_plugin_meme_studio` directory exists and has no `.git/`.

- [ ] **Step 2: Update plugin metadata**

Edit `metadata.yaml` to:

```yaml
name: "astrbot_plugin_meme_studio"
display_name: "Meme Studio 表情工作台"
author: "zhajunyao"
version: "2.1.0"
short_desc: "QQ 头像表情包生成与服务器模板工作台。"
desc: "支持群聊头像表情生成、本地/服务器浏览器模板制作、GIF 分解、模板预览、应用与删除。"
astrbot_version: ">=4.12.0"
repo: "https://github.com/zhajunyao/astrbot_plugin_meme_studio"
support_platforms:
  - aiocqhttp
```

- [ ] **Step 3: Update package builder name**

In `tools/package_plugin_zip.py`, set:

```python
PACKAGE_NAME = "astrbot_plugin_meme_studio"
OUTPUT = ROOT.parent / f"{PACKAGE_NAME}_install.zip"
```

- [ ] **Step 4: Update docs references**

Replace review-facing references to `astrbot_plugin_meme_manufacturer` with `astrbot_plugin_meme_studio` in `README.md` and `SECURITY_REVIEW.md`. Keep the old name only in migration notes when explicitly describing the previous repository.

- [ ] **Step 5: Initialize git and commit**

Run in the new root:

```powershell
git init -b main
git add .
git commit -m "chore: rename project to meme studio"
```

Expected: commit succeeds and `git status --short` is empty.

---

### Task 2: Split Command Registry Into `meme_studio/commands.py`

**Files:**
- Create: `meme_studio/__init__.py`
- Create: `meme_studio/commands.py`
- Modify: `meme_commands.py`
- Modify: `tools/generate_conf_schema.py`
- Modify: `tests/test_meme_commands.py`
- Modify: `tests/test_generated_meme_commands.py`

- [ ] **Step 1: Write failing import compatibility test**

Add to `tests/test_meme_commands.py`:

```python
def test_legacy_meme_commands_module_reexports_new_registry(self):
    import meme_commands
    from meme_studio import commands

    self.assertIs(meme_commands.MemeCommand, commands.MemeCommand)
    self.assertEqual(meme_commands.BUILTIN_MEME_COMMANDS, commands.BUILTIN_MEME_COMMANDS)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -B -m unittest tests.test_meme_commands.MemeCommandRegistryTest.test_legacy_meme_commands_module_reexports_new_registry -v
```

Expected before implementation: import fails because `meme_studio.commands` does not exist.

- [ ] **Step 3: Move command registry code**

Create `meme_studio/__init__.py`:

```python
"""Shared runtime and Meme Studio modules for the AstrBot meme plugin."""
```

Move the full command registry from `meme_commands.py` into `meme_studio/commands.py`, including:

```python
MemeCommand
BUILTIN_MEME_COMMANDS
load_generated_commands
all_meme_commands
build_conf_schema
```

Keep the existing validation helpers in the new file.

- [ ] **Step 4: Turn `meme_commands.py` into a compatibility shim**

Replace `meme_commands.py` with:

```python
try:
    from .meme_studio.commands import *  # noqa: F401,F403
except ImportError:
    from meme_studio.commands import *  # noqa: F401,F403
```

- [ ] **Step 5: Update direct imports**

Update `tools/generate_conf_schema.py` and tests to import from `meme_studio.commands` when possible. Keep `meme_commands.py` only for old import compatibility.

- [ ] **Step 6: Run command registry tests**

Run:

```bash
python -B -m unittest tests.test_meme_commands tests.test_generated_meme_commands -v
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```bash
git add meme_studio/__init__.py meme_studio/commands.py meme_commands.py tools/generate_conf_schema.py tests/test_meme_commands.py tests/test_generated_meme_commands.py
git commit -m "refactor: split command registry module"
```

---

### Task 3: Split Rendering Core Into `meme_studio/renderer.py`

**Files:**
- Create: `meme_studio/renderer.py`
- Modify: `meme_studio_core.py`
- Modify: `scripts/render_manifest_template.py`
- Modify: `tests/test_meme_studio_core.py`

- [ ] **Step 1: Write failing compatibility test**

Add to `tests/test_meme_studio_core.py`:

```python
def test_legacy_core_module_reexports_renderer_api(self):
    import meme_studio_core
    from meme_studio import renderer

    self.assertIs(meme_studio_core.validate_manifest, renderer.validate_manifest)
    self.assertIs(meme_studio_core.render_manifest, renderer.render_manifest)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_meme_studio_core.MemeStudioCoreTest.test_legacy_core_module_reexports_renderer_api -v
```

Expected before implementation: import fails because `meme_studio.renderer` does not exist.

- [ ] **Step 3: Move renderer code**

Move the full contents of `meme_studio_core.py` into `meme_studio/renderer.py`.

- [ ] **Step 4: Turn `meme_studio_core.py` into a compatibility shim**

Replace `meme_studio_core.py` with:

```python
try:
    from .meme_studio.renderer import *  # noqa: F401,F403
except ImportError:
    from meme_studio.renderer import *  # noqa: F401,F403
```

- [ ] **Step 5: Update render script import**

In `scripts/render_manifest_template.py`, import renderer functions with this fallback:

```python
try:
    from meme_studio.renderer import render_manifest
except ImportError:
    from meme_studio_core import render_manifest
```

- [ ] **Step 6: Run renderer tests**

```bash
python -B -m unittest tests.test_meme_studio_core -v
```

Expected: all renderer tests pass.

- [ ] **Step 7: Commit**

```bash
git add meme_studio/renderer.py meme_studio_core.py scripts/render_manifest_template.py tests/test_meme_studio_core.py
git commit -m "refactor: split renderer module"
```

---

### Task 4: Split Runtime Into `meme_studio/runtime.py`

**Files:**
- Create: `meme_studio/runtime.py`
- Modify: `main.py`
- Modify: `tests/test_main_registration.py`

- [ ] **Step 1: Write failing runtime import test**

Add to `tests/test_main_registration.py`:

```python
def test_main_uses_runtime_plugin_class(self):
    import main
    from meme_studio.runtime import MemeStudioRuntime

    self.assertIs(main.MemeStudioRuntime, MemeStudioRuntime)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_main_registration.MainRegistrationTest.test_main_uses_runtime_plugin_class -v
```

Expected before implementation: import fails because `meme_studio.runtime` does not exist.

- [ ] **Step 3: Move runtime code**

Create `meme_studio/runtime.py` by moving:

```python
TEMP_ROOT_NAME
STALE_JOB_MAX_AGE_SECONDS
SCRIPT_TIMEOUT_SECONDS
MAX_IMAGE_BYTES
HTTP_TIMEOUT
QQ_AVATAR_URL
ScriptResult
_clip_log_text
MemeArsenal class body
_make_astrbot_command_handler
_install_astrbot_command_handlers
```

Rename class `MemeArsenal` to `MemeStudioRuntime`.

- [ ] **Step 4: Keep AstrBot class name available**

At the end of `meme_studio/runtime.py`, add:

```python
MemeArsenal = MemeStudioRuntime
_install_astrbot_command_handlers()
```

- [ ] **Step 5: Make `main.py` a thin adapter**

Replace `main.py` with:

```python
try:
    from .meme_studio.runtime import MemeArsenal, MemeStudioRuntime
except ImportError:
    from meme_studio.runtime import MemeArsenal, MemeStudioRuntime

__all__ = ["MemeArsenal", "MemeStudioRuntime"]
```

- [ ] **Step 6: Update runtime imports**

In `meme_studio/runtime.py`, import commands with:

```python
try:
    from .commands import MemeCommand, all_meme_commands
except ImportError:
    from meme_studio.commands import MemeCommand, all_meme_commands
```

- [ ] **Step 7: Run runtime tests**

```bash
python -B -m unittest tests.test_main_registration -v
```

Expected: all runtime tests pass.

- [ ] **Step 8: Commit**

```bash
git add main.py meme_studio/runtime.py tests/test_main_registration.py
git commit -m "refactor: split AstrBot runtime module"
```

---

### Task 5: Split Studio Service And Server Modules

**Files:**
- Create: `meme_studio/studio_service.py`
- Create: `meme_studio/studio_server.py`
- Move directory: `tools/meme_studio/web/` to `meme_studio/web/`
- Modify: `tools/meme_studio/server.py`
- Modify: `tests/test_meme_studio_server.py`

- [ ] **Step 1: Write failing service import test**

Add to `tests/test_meme_studio_server.py`:

```python
def test_legacy_server_reexports_new_service(self):
    from meme_studio.studio_service import MemeStudioService
    from tools.meme_studio.server import MemeStudioService as LegacyMemeStudioService

    self.assertIs(LegacyMemeStudioService, MemeStudioService)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_meme_studio_server.MemeStudioServerTest.test_legacy_server_reexports_new_service -v
```

Expected before implementation: import fails because `meme_studio.studio_service` does not exist.

- [ ] **Step 3: Move service class**

Move `MemeStudioService` and helpers used by the service into `meme_studio/studio_service.py`. Use imports:

```python
from .commands import BUILTIN_MEME_COMMANDS, MemeCommand, build_conf_schema
from .renderer import decompose_gif_to_frames, image_to_frame, render_manifest, validate_command_name, validate_manifest
```

- [ ] **Step 4: Move HTTP server**

Move `create_server`, request handler logic, `_decode_uploads`, `_clip_preview_reason`, and `_normalize_preview_ext` into `meme_studio/studio_server.py`. Set:

```python
WEB_ROOT = Path(__file__).resolve().parent / "web"
```

- [ ] **Step 5: Move web assets**

Move:

```text
tools/meme_studio/web/app.js
tools/meme_studio/web/index.html
tools/meme_studio/web/styles.css
```

to:

```text
meme_studio/web/app.js
meme_studio/web/index.html
meme_studio/web/styles.css
```

- [ ] **Step 6: Keep legacy server wrapper**

Replace `tools/meme_studio/server.py` with:

```python
try:
    from meme_studio.studio_server import *  # noqa: F401,F403
    from meme_studio.studio_service import MemeStudioService
except ImportError:
    from ...meme_studio.studio_server import *  # noqa: F401,F403
    from ...meme_studio.studio_service import MemeStudioService
```

- [ ] **Step 7: Update tests imports**

In `tests/test_meme_studio_server.py`, import service from:

```python
from meme_studio.studio_service import MemeStudioService
```

- [ ] **Step 8: Run studio server tests**

```bash
python -B -m unittest tests.test_meme_studio_server -v
```

Expected: all studio service tests pass.

- [ ] **Step 9: Commit**

```bash
git add meme_studio/studio_service.py meme_studio/studio_server.py meme_studio/web tools/meme_studio/server.py tests/test_meme_studio_server.py
git add -u tools/meme_studio/web
git commit -m "refactor: split meme studio service and server"
```

---

### Task 6: Add Studio Token Security

**Files:**
- Create: `meme_studio/studio_security.py`
- Create: `tests/test_studio_security.py`
- Modify: `meme_studio/studio_server.py`
- Modify: `meme_studio/web/app.js`

- [ ] **Step 1: Write failing security tests**

Create `tests/test_studio_security.py`:

```python
import unittest

from meme_studio.studio_security import (
    StudioAuthConfig,
    extract_request_token,
    generate_access_token,
    is_public_bind_host,
    token_matches,
)


class StudioSecurityTest(unittest.TestCase):
    def test_generate_access_token_is_urlsafe_and_long(self):
        token = generate_access_token()

        self.assertGreaterEqual(len(token), 32)
        self.assertNotIn("/", token)
        self.assertNotIn("+", token)

    def test_public_bind_host_detection(self):
        self.assertTrue(is_public_bind_host("0.0.0.0"))
        self.assertTrue(is_public_bind_host("::"))
        self.assertFalse(is_public_bind_host("127.0.0.1"))
        self.assertFalse(is_public_bind_host("localhost"))

    def test_token_matches_uses_configured_token(self):
        config = StudioAuthConfig(token="secret")

        self.assertTrue(token_matches(config, "secret"))
        self.assertFalse(token_matches(config, "wrong"))

    def test_extract_request_token_accepts_bearer_and_query(self):
        self.assertEqual(extract_request_token("Bearer abc", ""), "abc")
        self.assertEqual(extract_request_token("", "token=abc"), "abc")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_studio_security -v
```

Expected before implementation: import fails because `meme_studio.studio_security` does not exist.

- [ ] **Step 3: Implement security helpers**

Create `meme_studio/studio_security.py`:

```python
import hmac
import secrets
from dataclasses import dataclass
from urllib.parse import parse_qs


@dataclass(frozen=True)
class StudioAuthConfig:
    token: str


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def is_public_bind_host(host: str) -> bool:
    normalized = host.strip().lower()
    return normalized in {"0.0.0.0", "::"} or normalized not in {"", "127.0.0.1", "::1", "localhost"}


def extract_request_token(authorization: str, query: str) -> str:
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    values = parse_qs(query).get("token", [])
    return values[0] if values else ""


def token_matches(config: StudioAuthConfig, provided: str) -> bool:
    return bool(provided) and hmac.compare_digest(config.token, provided)
```

- [ ] **Step 4: Integrate auth into server**

Change `create_server` signature in `meme_studio/studio_server.py`:

```python
def create_server(
    project_root: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    auth_config: Optional[StudioAuthConfig] = None,
) -> ThreadingHTTPServer:
```

In every `/api/` route, call:

```python
if not self._is_authorized(parsed):
    self._send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
    return
```

Add handler method:

```python
def _is_authorized(self, parsed) -> bool:
    if auth_config is None:
        return True
    token = extract_request_token(self.headers.get("Authorization", ""), parsed.query)
    return token_matches(auth_config, token)
```

- [ ] **Step 5: Update browser API client**

In `meme_studio/web/app.js`, add:

```javascript
const authToken = new URLSearchParams(window.location.search).get("token") || localStorage.getItem("memeStudioToken") || "";
if (authToken) localStorage.setItem("memeStudioToken", authToken);
```

Update `postJson` and `getJson` headers:

```javascript
const headers = {"Content-Type": "application/json"};
if (authToken) headers.Authorization = `Bearer ${authToken}`;
```

For `getJson`, send:

```javascript
const response = await fetch(url, {headers: authToken ? {Authorization: `Bearer ${authToken}`} : {}});
```

- [ ] **Step 6: Add server auth test**

Create a test in `tests/test_meme_studio_server.py` that instantiates `create_server(..., auth_config=StudioAuthConfig("secret"))`, calls `/api/templates` without auth, and asserts HTTP 401.

- [ ] **Step 7: Run security tests**

```bash
python -B -m unittest tests.test_studio_security tests.test_meme_studio_server -v
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit**

```bash
git add meme_studio/studio_security.py meme_studio/studio_server.py meme_studio/web/app.js tests/test_studio_security.py tests/test_meme_studio_server.py
git commit -m "feat: protect meme studio server with token auth"
```

---

### Task 7: Harden Upload Decoding

**Files:**
- Modify: `meme_studio/studio_security.py`
- Modify: `meme_studio/studio_server.py`
- Create: `tests/test_studio_uploads.py`

- [ ] **Step 1: Write failing upload tests**

Create `tests/test_studio_uploads.py`:

```python
import base64
import unittest

from meme_studio.studio_security import decode_uploads


class StudioUploadsTest(unittest.TestCase):
    def test_decode_uploads_rejects_invalid_base64(self):
        with self.assertRaises(ValueError):
            decode_uploads([{"name": "bad.png", "data": "not base64 !!!"}])

    def test_decode_uploads_normalizes_unsafe_names(self):
        payload = base64.b64encode(b"abc").decode("ascii")

        files = decode_uploads([{"name": "../evil.png", "data": payload}])

        self.assertEqual(files[0]["name"], "evil.png")
        self.assertEqual(files[0]["data"], b"abc")

    def test_decode_uploads_rejects_large_file(self):
        payload = base64.b64encode(b"a" * 12).decode("ascii")

        with self.assertRaises(ValueError):
            decode_uploads([{"name": "big.png", "data": payload}], max_file_bytes=8)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_studio_uploads -v
```

Expected before implementation: import fails because `decode_uploads` does not exist.

- [ ] **Step 3: Implement strict decoder**

Add to `meme_studio/studio_security.py`:

```python
import base64
import binascii
from pathlib import PurePath
from typing import Dict, List


DEFAULT_MAX_UPLOAD_FILES = 80
DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def safe_upload_name(name: str) -> str:
    clean = PurePath(str(name).replace("\\", "/")).name.strip()
    if not clean:
        raise ValueError("上传文件名为空")
    return clean


def decode_uploads(
    files: List[Dict[str, object]],
    max_files: int = DEFAULT_MAX_UPLOAD_FILES,
    max_file_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> List[Dict[str, object]]:
    if len(files) > max_files:
        raise ValueError("上传文件过多")
    decoded = []
    for file_info in files:
        raw = str(file_info["data"])
        if "," in raw:
            raw = raw.split(",", 1)[1]
        try:
            data = base64.b64decode(raw, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("上传文件不是有效 Base64") from exc
        if len(data) > max_file_bytes:
            raise ValueError("上传文件过大")
        decoded.append({"name": safe_upload_name(str(file_info["name"])), "data": data})
    return decoded
```

- [ ] **Step 4: Use decoder in server**

In `meme_studio/studio_server.py`, replace `_decode_uploads(...)` calls with imported `decode_uploads(...)`, and remove the old `_decode_uploads` helper.

- [ ] **Step 5: Run upload and server tests**

```bash
python -B -m unittest tests.test_studio_uploads tests.test_meme_studio_server -v
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add meme_studio/studio_security.py meme_studio/studio_server.py tests/test_studio_uploads.py
git commit -m "feat: harden meme studio uploads"
```

---

### Task 8: Update Linux Launcher For Token Mode

**Files:**
- Modify: `meme_studio_launcher.py`
- Modify: `tools/meme_studio.py`
- Modify: `tests/test_meme_studio_launcher.py`

- [ ] **Step 1: Write failing launcher tests**

Add to `tests/test_meme_studio_launcher.py`:

```python
def test_build_server_url_includes_token_when_present(self):
    from meme_studio_launcher import build_server_url

    self.assertEqual(
        build_server_url("0.0.0.0", 8765, "abc"),
        "http://0.0.0.0:8765/?token=abc",
    )

def test_public_bind_generates_token_when_missing(self):
    from meme_studio_launcher import resolve_auth_config

    auth = resolve_auth_config("0.0.0.0", "")

    self.assertTrue(auth.token)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_meme_studio_launcher -v
```

Expected before implementation: new functions are missing.

- [ ] **Step 3: Update launcher imports**

In `meme_studio_launcher.py`, import:

```python
from meme_studio.studio_security import StudioAuthConfig, generate_access_token, is_public_bind_host
```

- [ ] **Step 4: Add launcher helpers**

Add:

```python
def resolve_auth_config(host: str, token: str) -> StudioAuthConfig:
    value = token.strip() if token else ""
    if not value:
        value = generate_access_token()
    return StudioAuthConfig(value)


def build_server_url(host: str, port: int, token: str) -> str:
    url = f"http://{host}:{port}/"
    return f"{url}?token={token}" if token else url
```

- [ ] **Step 5: Add CLI option**

In `main()`, add:

```python
parser.add_argument("--token", default="", help="Meme Studio 访问令牌；不填则自动生成")
```

Use:

```python
auth_config = resolve_auth_config(args.host, args.token)
server = create_server(project_root, args.host, port, auth_config=auth_config)
url = build_server_url(args.host, port, auth_config.token)
```

Print:

```python
print(f"Meme Studio running at {url}", flush=True)
if is_public_bind_host(args.host):
    print("Security: token authentication is enabled. Do not share the URL publicly.", flush=True)
```

- [ ] **Step 6: Update server import**

In launcher, import server from:

```python
from meme_studio.studio_server import create_server
```

- [ ] **Step 7: Run launcher tests**

```bash
python -B -m unittest tests.test_meme_studio_launcher -v
```

Expected: all launcher tests pass.

- [ ] **Step 8: Commit**

```bash
git add meme_studio_launcher.py tools/meme_studio.py tests/test_meme_studio_launcher.py
git commit -m "feat: add token-aware Linux studio launcher"
```

---

### Task 9: Update Browser UI Paths And Auth Behavior

**Files:**
- Modify: `meme_studio/web/app.js`
- Modify: `meme_studio/web/index.html`
- Modify: `meme_studio/web/styles.css`
- Modify: `tests/test_meme_studio_web.py`

- [ ] **Step 1: Write failing web test**

Add to `tests/test_meme_studio_web.py`:

```python
def test_web_client_sends_bearer_token(self):
    script = Path("meme_studio/web/app.js").read_text(encoding="utf-8")

    self.assertIn("Authorization", script)
    self.assertIn("Bearer", script)
    self.assertIn("memeStudioToken", script)
```

- [ ] **Step 2: Run test to verify it fails or confirms current gap**

```bash
python -B -m unittest tests.test_meme_studio_web.MemeStudioWebTest.test_web_client_sends_bearer_token -v
```

Expected before Task 6 implementation: fails because token handling is absent. If Task 6 already added token handling, this test passes and should be kept as regression coverage.

- [ ] **Step 3: Keep UI as app-first studio**

Ensure `meme_studio/web/index.html` opens directly into the editing workspace. It must not add a marketing hero page.

- [ ] **Step 4: Ensure delete confirmation remains explicit**

In `meme_studio/web/app.js`, keep:

```javascript
const confirmed = window.confirm(`确认删除 /${template.name} 吗？`);
if (!confirmed) return;
```

- [ ] **Step 5: Ensure GIF previews stay animated**

Template preview elements should use normal image loading:

```javascript
preview.src = `${template.preview_url}?v=${Date.now()}`;
```

Do not draw template GIF previews onto a canvas for the list view.

- [ ] **Step 6: Run web syntax and tests**

```bash
node --check meme_studio/web/app.js
python -B -m unittest tests.test_meme_studio_web -v
```

Expected: Node syntax check exits 0 and web tests pass.

- [ ] **Step 7: Commit**

```bash
git add meme_studio/web tests/test_meme_studio_web.py
git commit -m "feat: update studio web auth client"
```

---

### Task 10: Update Packaging And Package Tests

**Files:**
- Modify: `tools/package_plugin_zip.py`
- Create: `tests/test_package_plugin_zip.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing package test**

Create `tests/test_package_plugin_zip.py`:

```python
import zipfile
import unittest

from tools import package_plugin_zip


class PackagePluginZipTest(unittest.TestCase):
    def test_archive_name_uses_new_package_name(self):
        path = package_plugin_zip.ROOT / "main.py"

        self.assertEqual(
            package_plugin_zip.archive_name(path),
            "astrbot_plugin_meme_studio/main.py",
        )

    def test_excludes_local_runtime_artifacts(self):
        excluded = [
            package_plugin_zip.ROOT / "MemeStudio.exe",
            package_plugin_zip.ROOT / "tests" / "test_package_plugin_zip.py",
            package_plugin_zip.ROOT / ".meme_studio_sessions" / "x",
            package_plugin_zip.ROOT / "build" / "x",
        ]

        self.assertTrue(all(not package_plugin_zip.should_include(path) for path in excluded))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -B -m unittest tests.test_package_plugin_zip -v
```

Expected before implementation: package name assertion fails if the old name remains.

- [ ] **Step 3: Update package script**

Ensure:

```python
PACKAGE_NAME = "astrbot_plugin_meme_studio"
EXCLUDE_DIRS = {
    ".git",
    ".meme_studio_sessions",
    ".meme_studio_previews",
    "__pycache__",
    "build",
    "dist",
    "docs",
    "exports",
    "tests",
}
EXCLUDE_FILES = {
    ".gitignore",
    ".gitattributes",
    "MemeStudio.exe",
}
EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".spec",
}
```

- [ ] **Step 4: Run package tests**

```bash
python -B -m unittest tests.test_package_plugin_zip -v
```

Expected: package tests pass.

- [ ] **Step 5: Build zip and inspect**

```bash
python tools/package_plugin_zip.py
```

Expected output includes:

```text
created ...\astrbot_plugin_meme_studio_install.zip
```

Inspect zip:

```powershell
$zip = '..\astrbot_plugin_meme_studio_install.zip'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $zip).Path)
try {
  $bad = $archive.Entries.FullName | Where-Object { $_ -match '(^|/)(\.git|__pycache__|tests|docs)(/|$)' -or $_ -match '\.(exe|pyc|pyo|spec)$' }
  if ($bad) { throw "Unexpected entries: $($bad -join ', ')" }
  "zip ok"
}
finally { $archive.Dispose() }
```

- [ ] **Step 6: Commit**

```bash
git add tools/package_plugin_zip.py tests/test_package_plugin_zip.py .gitignore
git commit -m "chore: update meme studio packaging"
```

---

### Task 11: Update README And Security Review

**Files:**
- Modify: `README.md`
- Modify: `SECURITY_REVIEW.md`

- [ ] **Step 1: Update README with Linux-first server workflow**

Add this command block near installation or Meme Studio usage:

```bash
cd /AstrBot/data/plugins/astrbot_plugin_meme_studio
python tools/meme_studio.py --host 0.0.0.0 --port 8765 --no-open
```

Explain that the terminal prints a tokenized URL and that the token should not be shared publicly.

- [ ] **Step 2: Update README plugin collection payload**

Use:

```json
{
  "name": "astrbot_plugin_meme_studio",
  "display_name": "Meme Studio 表情工作台",
  "desc": "QQ 头像表情包生成与服务器模板工作台，支持 GIF 分解、模板预览、应用与删除。",
  "author": "zhajunyao",
  "repo": "https://github.com/zhajunyao/astrbot_plugin_meme_studio",
  "tags": ["娱乐", "表情包", "图片"],
  "social_link": "https://github.com/zhajunyao"
}
```

- [ ] **Step 3: Update security review**

Add a section:

```markdown
## Meme Studio 管理台

- 默认绑定 `127.0.0.1`。
- 绑定 `0.0.0.0` 等公开地址时，终端启动器会生成访问令牌。
- API 请求通过 `Authorization: Bearer <token>` 或 URL token 校验。
- 未授权 API 请求返回 HTTP 401。
- 管理台只能删除生成模板，不能删除内置模板。
```

- [ ] **Step 4: Scan docs for old repository name**

```powershell
Select-String -Path README.md,SECURITY_REVIEW.md,metadata.yaml,tools/package_plugin_zip.py -Pattern 'astrbot_plugin_meme_manufacturer'
```

Expected: no matches except intentional migration references in README.

- [ ] **Step 5: Commit**

```bash
git add README.md SECURITY_REVIEW.md metadata.yaml
git commit -m "docs: update meme studio review documentation"
```

---

### Task 12: Full Verification

**Files:**
- No source changes unless verification finds a bug.

- [ ] **Step 1: Run full unit tests**

```bash
python -B -m unittest discover -v
```

Expected: all tests pass.

- [ ] **Step 2: Run Python compile check**

```bash
python -m compileall -q .
```

Expected: exit code 0.

- [ ] **Step 3: Run web syntax check**

```bash
node --check meme_studio/web/app.js
```

Expected: exit code 0.

- [ ] **Step 4: Build package**

```bash
python tools/package_plugin_zip.py
```

Expected: `astrbot_plugin_meme_studio_install.zip` is created.

- [ ] **Step 5: Verify git status**

```bash
git status --short --branch
```

Expected: clean branch, or only the generated install zip outside the repository root.

- [ ] **Step 6: Commit verification fixes only if needed**

If verification required source changes:

```bash
git add <changed files>
git commit -m "fix: address verification issues"
```

If no source changes were needed, do not create an empty commit.

---

### Task 13: Create GitHub Repository And Push

**Files:**
- Git remote configuration only.

- [ ] **Step 1: Create GitHub repository**

Create:

```text
https://github.com/zhajunyao/astrbot_plugin_meme_studio
```

The repository should be public and initially empty.

- [ ] **Step 2: Add remote**

```bash
git remote add origin https://github.com/zhajunyao/astrbot_plugin_meme_studio.git
```

If `origin` already exists and points elsewhere:

```bash
git remote set-url origin https://github.com/zhajunyao/astrbot_plugin_meme_studio.git
```

- [ ] **Step 3: Push main branch**

```bash
git push -u origin main
```

Expected:

```text
branch 'main' set up to track 'origin/main'
```

- [ ] **Step 4: Verify remote branch**

```bash
git ls-remote --heads origin
```

Expected: `refs/heads/main` points to the latest local commit.

---

### Task 14: Optional Release Artifact

**Files:**
- No repository source changes.

- [ ] **Step 1: Create tag**

```bash
git tag v2.1.0
git push origin v2.1.0
```

- [ ] **Step 2: Attach package zip**

Attach:

```text
C:\Users\35559\Documents\Codex\2026-06-04\f-astrbot-plugin-meme-manufacturer-astrbot\publish\astrbot_plugin_meme_studio_install.zip
```

to GitHub Release `v2.1.0`.

- [ ] **Step 3: Keep executable optional**

If a Windows executable is generated, attach it only as an optional release artifact. Do not commit `MemeStudio.exe` to the repository.

---

## Spec Coverage Check

- New repository name: Task 1, Task 13.
- Runtime/studio separation: Task 2 through Task 5.
- Linux terminal browser workflow: Task 8, Task 11.
- Token protection: Task 6, Task 8, Task 9, Task 11.
- Template create/list/delete/apply behavior: Task 5, Task 6, existing service tests.
- Upload hardening: Task 7.
- Packaging boundary: Task 10, Task 12.
- Review documentation: Task 11.

## Completion Criteria

The rebuild is complete when:

- `python -B -m unittest discover -v` passes.
- `python -m compileall -q .` passes.
- `node --check meme_studio/web/app.js` passes.
- `python tools/package_plugin_zip.py` creates `astrbot_plugin_meme_studio_install.zip`.
- The zip contains no `.git`, tests, docs, cache files, executable binaries, or Python bytecode.
- GitHub repository `zhajunyao/astrbot_plugin_meme_studio` exists and has the rebuilt source on `main`.
- README and `SECURITY_REVIEW.md` describe the Linux server startup and token-protected API clearly.
