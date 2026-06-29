# Meme Studio Rebuild Design

## Goal

Rebuild the current `astrbot_plugin_meme_manufacturer` into a cleaner, review-ready AstrBot plugin named `astrbot_plugin_meme_studio`. The new project should keep the existing meme generation behavior while separating the bot runtime from the browser-based template studio, so a Linux server operator can start a protected web studio from the terminal, create templates in the browser, and apply them directly to the running bot plugin files.

## Repository Name

The new public repository should be:

```text
zhajunyao/astrbot_plugin_meme_studio
```

The old repository should remain archived or renamed as legacy history. Official AstrBot plugin review should use the new repository URL to avoid carrying previous failed-review history.

## Product Shape

The project has one installable AstrBot plugin with two clearly separated entry points.

1. Bot runtime
   - Loaded by AstrBot through `main.py`.
   - Handles group commands such as `/摸 @某人`.
   - Downloads avatars or message images.
   - Runs rendering scripts in bounded subprocesses.
   - Sends generated PNG/GIF output back to chat.

2. Meme Studio management console
   - Started manually from the server terminal.
   - Opens a browser UI for template creation and management.
   - Lists builtin and generated templates with previews.
   - Creates static PNG or GIF templates.
   - Decomposes GIF uploads into frames.
   - Applies generated templates into the plugin's `data/`, `generated_meme_commands.json`, and `_conf_schema.json`.
   - Deletes only generated templates after explicit confirmation.

This keeps installation simple: users install one plugin, but maintainers can review the runtime and management console as separate components.

## Linux Server Workflow

The Linux server workflow should be first-class:

```bash
cd /AstrBot/data/plugins/astrbot_plugin_meme_studio
python tools/meme_studio.py --host 0.0.0.0 --port 8765 --no-open
```

When no token is supplied, the launcher should generate a one-time token and print a URL like:

```text
Meme Studio running at http://0.0.0.0:8765/?token=<token>
```

Users can also supply a stable token:

```bash
python tools/meme_studio.py --host 0.0.0.0 --port 8765 --token "change-me" --no-open
```

For local Windows use, the existing simple command should still work:

```bash
python tools/meme_studio.py
```

The launcher should bind to `127.0.0.1` by default. Binding to `0.0.0.0` should be explicit.

## Security Model

The browser console can write plugin files, so it needs a clear safety boundary.

### HTTP Access

- `127.0.0.1` mode may run without an explicit token, but generated token mode is still preferred.
- Non-localhost hosts must require a token.
- API requests must validate the token through an `Authorization: Bearer <token>` header or `?token=<token>` query string.
- Static HTML/CSS/JS can be served without token only if the API remains protected. The UI should store the token from the URL in memory or local storage and send it with all API requests.
- Failed API authentication returns HTTP 401 with JSON.

### Uploads

- JSON request size remains bounded.
- File count and file byte size are bounded.
- Upload decode uses strict Base64 validation.
- Uploaded file names are normalized to safe names before writing.
- Accepted inputs remain image formats that Pillow can parse.

### Paths

- Session directories stay under `.meme_studio_sessions/`.
- Preview cache stays under `.meme_studio_previews/`.
- Export directory stays under `exports/`.
- Applied generated templates stay under `data/<safe-command>/`.
- Generated manifest paths stay in `data/<safe-command>/manifest.json`.
- Builtin templates cannot be deleted by the studio.

### Rendering

- Builtin script previews and runtime rendering use subprocess argument lists, not shell strings.
- Script paths are resolved and constrained to `scripts/`.
- Rendering timeouts are enforced.
- Temporary directories are cleaned after use.

## Code Architecture

The current project should be reorganized into clearer modules while preserving AstrBot compatibility.

```text
astrbot_plugin_meme_studio/
├─ main.py
├─ meme_studio/
│  ├─ __init__.py
│  ├─ commands.py
│  ├─ runtime.py
│  ├─ renderer.py
│  ├─ studio_service.py
│  ├─ studio_server.py
│  ├─ studio_security.py
│  └─ web/
│     ├─ index.html
│     ├─ app.js
│     └─ styles.css
├─ tools/
│  ├─ meme_studio.py
│  ├─ build_meme_studio_exe.py
│  ├─ generate_conf_schema.py
│  └─ package_plugin_zip.py
├─ data/
├─ scripts/
├─ tests/
├─ metadata.yaml
├─ README.md
├─ SECURITY_REVIEW.md
└─ requirements.txt
```

### Module Responsibilities

- `main.py`: minimal AstrBot adapter, imports and installs runtime handlers.
- `meme_studio/commands.py`: builtin and generated command registry.
- `meme_studio/runtime.py`: image source resolution, avatar download, subprocess execution, chat output.
- `meme_studio/renderer.py`: manifest validation, template rendering, GIF decomposition.
- `meme_studio/studio_service.py`: template upload, export, apply, list, delete, preview.
- `meme_studio/studio_server.py`: HTTP routing and JSON/static responses.
- `meme_studio/studio_security.py`: token generation, auth validation, safe upload and path helpers.
- `tools/meme_studio.py`: terminal launcher for local and Linux server mode.
- `tools/package_plugin_zip.py`: review-safe AstrBot install package builder.

This split removes the current "large script with many responsibilities" feeling and gives reviewers focused files to inspect.

## Browser UI

The existing Meme Studio UI should stay as the main experience, but the interface should be adjusted around three panels:

1. Template editor
   - Command name.
   - Prompt message.
   - Output type: PNG or GIF.
   - Avatar shape.
   - Upload image/GIF.
   - Drag and resize avatar slot.
   - Preview current result.

2. Bot templates
   - Builtin and generated template list.
   - Live preview thumbnails; GIF previews should animate.
   - Generated templates show delete action.
   - Builtin templates show readonly state.

3. Result and actions
   - Export local.
   - Apply to bot.
   - Show file path and reload reminder.

No marketing hero page is needed. The first screen should be the working studio.

## Plugin Metadata

Use the new identity:

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

Suggested official plugin collection payload:

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

## Packaging

The plugin market zip should include runtime source, studio source, web assets, scripts, data, metadata, README, security review, and requirements.

It should exclude:

- `.git/`
- `tests/`
- `docs/`
- `__pycache__/`
- `.meme_studio_sessions/`
- `.meme_studio_previews/`
- `exports/`
- `build/`
- `dist/`
- `MemeStudio.exe`
- `.pyc`, `.pyo`, `.spec`

`MemeStudio.exe` may be provided as an optional GitHub Release artifact, but not in the plugin market package.

## Testing Requirements

The rebuild should keep or add tests for:

- Command registry uniqueness.
- Generated command manifest path validation.
- Runtime remote image URL protection.
- Runtime local file and Base64 size limits.
- Studio upload GIF decomposition.
- Studio apply writes `data/`, `generated_meme_commands.json`, and `_conf_schema.json`.
- Studio list returns builtin and generated templates.
- Studio delete removes only generated templates.
- Studio previews preserve animated GIF previews.
- Server token auth rejects unauthenticated API writes.
- Server launcher requires token when binding to public interfaces.
- Package zip excludes unsafe files.

## Review Strategy

The README should lead with what the plugin does and how to run it on Linux:

```bash
python tools/meme_studio.py --host 0.0.0.0 --port 8765 --no-open
```

`SECURITY_REVIEW.md` should explicitly explain:

- No shell string execution.
- Script path confinement.
- URL private-network rejection.
- Upload size limits.
- Token-protected studio API.
- Generated template path confinement.
- Packaging excludes executable binaries and runtime caches.

This gives AstrBot reviewers a direct map of the logic and safety boundaries, instead of making them infer intent from a large mixed script.

## Migration Plan

1. Create a new repository named `astrbot_plugin_meme_studio`.
2. Copy the current clean source as the base.
3. Rename metadata, package name, README references, temp directory names, and security review references.
4. Split the code into the `meme_studio/` package.
5. Add token-protected server mode.
6. Update browser JS to send auth tokens.
7. Update tests for the new module paths and new security behavior.
8. Generate a fresh package zip.
9. Push to GitHub.
10. Use the new repository URL for official AstrBot plugin review.

## Out of Scope

- Hosting the studio as a permanent public web service.
- Multi-user accounts or role permissions.
- Remote editing of multiple AstrBot instances.
- Automatic AstrBot process restart from the browser.
- Bundling a Windows executable inside the plugin repository or market zip.
