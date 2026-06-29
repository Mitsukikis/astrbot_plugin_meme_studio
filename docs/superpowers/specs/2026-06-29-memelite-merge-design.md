# Meme Generator Merge Design

## Context

The user installed `Zhalslar/astrbot_plugin_memelite` and wants Meme Studio to learn from that plugin because it exposes a much larger meme catalog. The reference plugin is useful architecturally: it keeps a small AstrBot layer, delegates meme discovery/rendering to `meme-generator`, and separates parameter collection from meme management.

The reference repository's `LICENSE` is AGPL-3.0. Meme Studio will not copy its implementation. This work will use the public `meme-generator` package as an optional runtime dependency and implement a clean adapter in this project.

## Goals

- Keep the existing visual studio and generated-template runtime working.
- Add a second engine that can use `meme-generator` memes for a larger catalog.
- Use local/generated Meme Studio templates first when a command name conflicts.
- Make the new engine optional and failure-tolerant: missing resources or dependency errors must not break local templates.
- Keep review risk low with small modules, explicit configuration, bounded downloads, timeouts, tests, and clear documentation.

## Non-Goals

- Do not vendor or copy `astrbot_plugin_memelite` code.
- Do not bundle thousands of meme-generator assets inside this repository.
- Do not make every ordinary chat message fuzzy-match memes by default.
- Do not add a new web UI for browsing all meme-generator memes in this phase.

## Architecture

Meme Studio will have two runtime engines:

1. `MemeStudioRuntime` local engine: existing generated templates and built-in script templates.
2. `MemeGeneratorRuntime` optional engine: wraps `meme-generator`, loads its catalog, collects AstrBot message parameters, and returns generated image bytes.

`meme_studio/runtime.py` remains the AstrBot entrypoint. It first tries the local template command matcher. If no local command matches, it passes the message to `MemeGeneratorRuntime`. This preserves existing commands and avoids surprising conflicts.

The new engine lives in focused files:

- `meme_studio/generator_engine.py`: lazy import and compatibility wrapper around `meme-generator`.
- `meme_studio/generator_params.py`: collect images, text, and options from AstrBot events.
- `meme_studio/generator_runtime.py`: trigger policy, timeout, help/detail/blacklist commands, and output handling.

## Trigger Policy

Default behavior is safe:

- `generator_enabled`: true.
- `generator_need_prefix`: true.
- `generator_extra_prefix`: empty string.
- `generator_fuzzy_match`: false.

With default settings, users trigger generator memes with a slash-style command such as `/摸 @someone` or by waking/mentioning the bot according to AstrBot's event state. Administrators can disable prefix requirements or enable fuzzy matching, but the default should avoid accidental spam.

## Configuration

Add review-friendly config keys:

- `generator_enabled`: enable the optional generator engine.
- `generator_need_prefix`: require `/`, full-width slash, or bot wake/mention before matching generator memes.
- `generator_extra_prefix`: optional extra prefix stripped before generator matching.
- `generator_fuzzy_match`: allow keyword containment matching.
- `generator_check_resources`: check/download generator resources on startup.
- `generator_timeout_seconds`: generation timeout.
- `generator_compress_static`: compress large static outputs.
- `generator_disabled_list`: disabled generator meme keywords.

Existing per-template booleans remain unchanged.

## Resource Handling

`meme-generator` manages its own assets. Meme Studio will call its resource check in a background startup task when enabled. Errors are logged and do not stop plugin startup. Meme matching returns no result until the catalog is available.

Image downloads for avatars or message images must use the existing security posture: bounded byte reads, timeouts, no local network access for arbitrary remote images, and no unbounded file reads.

## Command Surface

Generator command surface:

- `/meme帮助`, `/表情帮助`, `/meme菜单`, `/meme列表`: render meme-generator catalog image if available.
- `/meme详情 <keyword>`, `/表情详情 <keyword>`, `/meme信息 <keyword>`: show metadata and preview.
- `/禁用meme <keyword>`: add keyword to generator disabled list.
- `/启用meme <keyword>`: remove keyword from generator disabled list.
- `/meme黑名单`: show disabled keywords.
- `/<keyword> [@user] [text] [key=value]`: generate one meme.

Local/generated template commands keep their current command names and continue to use existing slash behavior.

## Error Handling

- Missing `meme-generator`: log once and ignore generator requests.
- Resource check failure: warn, keep local templates active.
- Unknown generator keyword: silently ignore in passive handling; command/detail routes return a short user-facing message.
- Generation timeout: return a concise timeout message.
- Invalid image/download: return a concise image-read failure.
- Unexpected exception: log with stack trace and return a generic plugin error.

## Testing Strategy

Tests should not require `meme-generator` or network access. New tests use fake meme objects and fake event/message components.

Required coverage:

- Keyword matching exact/fuzzy and disabled keywords.
- Local template commands win over generator keywords.
- Generator engine missing dependency is non-fatal.
- Parameter collector uses sender avatar fallback only when needed.
- Help/detail methods unwrap bytes safely for bytes and `BytesIO`.
- Runtime timeout and static compression behavior are isolated.

## Documentation

README and SECURITY_REVIEW must explain:

- This project does not copy memelite source.
- `meme-generator` is an optional engine dependency.
- Linux/Docker may require graphics libraries for `meme-generator`.
- How to disable the engine if a server cannot install its dependencies.
- Local template commands have priority over generator commands.

## Acceptance

- Existing local template tests still pass.
- New generator tests pass without installing `meme-generator`.
- Full `unittest discover` passes.
- `requirements.txt`, `_conf_schema.json`, README, and SECURITY_REVIEW are consistent.
- GitHub repository remains a clean, reviewable plugin with no generated caches or bundled external meme assets.
