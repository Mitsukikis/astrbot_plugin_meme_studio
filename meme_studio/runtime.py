import asyncio
import base64
import binascii
import ipaddress
import os
import shutil
import socket
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence
from urllib.parse import unquote, urlparse

import httpx
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import At, Image
from astrbot.api.star import Context, Star

try:
    from .commands import MemeCommand, all_meme_commands
    from .generator_engine import GeneratorEngine
    from .generator_runtime import GeneratorRuntimeConfig, MemeGeneratorRuntime
except ImportError:
    from meme_studio.commands import MemeCommand, all_meme_commands
    from meme_studio.generator_engine import GeneratorEngine
    from meme_studio.generator_runtime import GeneratorRuntimeConfig, MemeGeneratorRuntime


TEMP_ROOT_NAME = "astrbot_plugin_meme_studio"
STALE_JOB_MAX_AGE_SECONDS = 6 * 60 * 60
SCRIPT_TIMEOUT_SECONDS = 120
MAX_IMAGE_BYTES = 25 * 1024 * 1024
HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=15.0, pool=5.0)
QQ_AVATAR_URL = "http://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"


@dataclass(frozen=True)
class ScriptResult:
    returncode: int
    stdout: str
    stderr: str


def _clip_log_text(text: str, limit: int = 1200) -> str:
    if len(text) <= limit:
        return text
    return "{}...".format(text[:limit])


class MemeStudioRuntime(Star):
    def __init__(self, context: Context, config: Optional[Dict[str, object]] = None):
        super().__init__(context)
        self.config = config or {}
        self.plugin_dir = Path(__file__).resolve().parents[1]
        self.scripts_dir = self.plugin_dir / "scripts"
        self.temp_root = Path(tempfile.gettempdir()) / TEMP_ROOT_NAME
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self._cleanup_stale_jobs()
        self.generator_runtime = MemeGeneratorRuntime(
            GeneratorEngine(),
            GeneratorRuntimeConfig.from_mapping(self.config),
            qq_avatar_source=self._qq_avatar_source,
        )

    def _cleanup_stale_jobs(self) -> None:
        now = time.time()
        for path in self.temp_root.iterdir():
            try:
                modified_at = path.stat().st_mtime
            except OSError:
                continue

            if now - modified_at > STALE_JOB_MAX_AGE_SECONDS:
                self._remove_path(path)

    def _remove_path(self, path: Path) -> None:
        try:
            if path.is_dir():
                shutil.rmtree(str(path))
            elif path.exists():
                path.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            logger.warning("清理临时文件失败: %s", exc)

    def _make_job_dir(self, command_name: str) -> Path:
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in command_name)
        safe_name = safe_name.strip("_") or "meme"
        return Path(tempfile.mkdtemp(prefix="{}_".format(safe_name), dir=str(self.temp_root)))

    def _is_command_enabled(self, command_name: str) -> bool:
        value = self.config.get(command_name, True)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in {"false", "0", "no", "off", "关闭"}
        return bool(value)

    def _normalize_local_path(self, source: str) -> Path:
        if source.startswith("file://"):
            parsed = urlparse(source)
            path = unquote(parsed.path)
            if os.name == "nt" and len(path) > 2 and path[0] == "/" and path[2] == ":":
                path = path[1:]
            return Path(path)
        return Path(source)

    async def _save_image_source(self, source: str, destination: Path) -> None:
        if source.startswith(("http://", "https://")):
            await self._download_image(source, destination)
            return

        if source.startswith("base64://"):
            self._save_base64_image(source, destination)
            return

        local_path = self._normalize_local_path(source)
        if local_path.exists() and local_path.is_file():
            self._copy_local_image(local_path, destination)
            return

        raise FileNotFoundError("无法读取图片源")

    async def _read_image_source_bytes(self, source: str) -> bytes:
        job_dir = self._make_job_dir("generator_source")
        source_path = job_dir / "source.image"
        try:
            await self._save_image_source(source, source_path)
            return source_path.read_bytes()
        finally:
            self._remove_path(job_dir)

    async def _download_image(self, url: str, destination: Path) -> None:
        self._validate_remote_image_url(url)
        total = 0
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with destination.open("wb") as file:
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > MAX_IMAGE_BYTES:
                            raise ValueError("图片文件过大")
                        file.write(chunk)

    def _validate_remote_image_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("不支持的图片地址协议")
        if not parsed.hostname:
            raise ValueError("图片地址缺少主机名")

        host = parsed.hostname.encode("idna").decode("ascii")
        for address in self._resolve_host_addresses(host):
            ip = ipaddress.ip_address(address)
            if not ip.is_global:
                raise ValueError("不允许访问内网或保留地址")

    @staticmethod
    def _resolve_host_addresses(host: str) -> Sequence[str]:
        try:
            return (str(ipaddress.ip_address(host)),)
        except ValueError:
            pass

        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        addresses = sorted({info[4][0] for info in infos})
        if not addresses:
            raise ValueError("无法解析图片地址")
        return tuple(addresses)

    def _copy_local_image(self, source: Path, destination: Path) -> None:
        if source.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("图片文件过大")
        shutil.copyfile(str(source), str(destination))

    def _save_base64_image(self, source: str, destination: Path) -> None:
        payload = source[len("base64://") :]
        image_bytes = base64.b64decode(payload, validate=True)
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise ValueError("图片文件过大")
        destination.write_bytes(image_bytes)

    def _qq_avatar_source(self, qq: object) -> str:
        return QQ_AVATAR_URL.format(qq=qq)

    def _pick_target_source(self, event: AstrMessageEvent) -> Optional[str]:
        message = getattr(event.message_obj, "message", []) or []

        for component in message:
            if isinstance(component, Image):
                url = getattr(component, "url", None)
                if url:
                    return url
                file = getattr(component, "file", None)
                if file:
                    return file

        self_id = str(event.get_self_id())
        for component in message:
            if isinstance(component, At) and str(component.qq) != self_id:
                return self._qq_avatar_source(component.qq)

        return None

    def _resolve_script_path(self, command: MemeCommand) -> Path:
        script_path = (self.scripts_dir / command.script).resolve()
        try:
            script_path.relative_to(self.scripts_dir.resolve())
        except ValueError:
            raise ValueError("非法脚本路径")

        if not script_path.is_file():
            raise FileNotFoundError("表情包脚本不存在")
        return script_path

    async def _run_script(self, args: Sequence[str]) -> ScriptResult:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(self.plugin_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            raise

        return ScriptResult(
            returncode=process.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace").strip(),
            stderr=stderr.decode("utf-8", errors="replace").strip(),
        )

    def _find_output_file(self, out_base: Path, preferred_ext: str) -> Optional[Path]:
        checked = set()
        for ext in (preferred_ext, "gif", "png"):
            if ext in checked:
                continue
            checked.add(ext)

            candidate = out_base.with_suffix(".{}".format(ext))
            if candidate.is_file():
                return candidate
        return None

    def _build_image_result(self, event: AstrMessageEvent, output_path: Path):
        image_bytes = output_path.read_bytes()
        result = event.make_result()
        result.chain = [Image.fromBytes(image_bytes)]
        return result

    def _commands_by_name(self) -> Dict[str, MemeCommand]:
        return {command.name: command for command in all_meme_commands() if command.name}

    @staticmethod
    def _has_command_boundary(message_body: str, command_name: str) -> bool:
        if message_body == command_name:
            return True
        if not message_body.startswith(command_name):
            return False

        suffix = message_body[len(command_name) :]
        if not suffix:
            return True

        first = suffix[0]
        return first.isspace() or first in {"@", "[", "<", "\u200b", "\u200c", "\u200d", "\ufeff"}

    def _match_command(self, event: AstrMessageEvent) -> Optional[MemeCommand]:
        message_text = getattr(event, "message_str", "") or getattr(
            event.message_obj,
            "message_str",
            "",
        )
        message_text = message_text.strip()
        if not message_text or message_text[0] not in {"/", "／"}:
            return None

        message_body = message_text[1:].lstrip()
        if not message_body:
            return None

        commands_by_name = self._commands_by_name()
        first_token = message_body.split(maxsplit=1)[0].strip()
        if first_token in commands_by_name:
            return commands_by_name[first_token]

        commands = sorted(commands_by_name.values(), key=lambda command: len(command.name), reverse=True)
        for command in commands:
            if self._has_command_boundary(message_body, command.name):
                return command

        return None

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        command = self._match_command(event)
        if command is not None:
            async for result in self._handle(event, command):
                yield result
            return

        async for result in self.generator_runtime.handle(event, self._read_image_source_bytes):
            yield result

    async def _handle(self, event: AstrMessageEvent, command: MemeCommand):
        if not self._is_command_enabled(command.name):
            yield event.plain_result("提示：管理员已禁用「{}」功能。".format(command.name))
            return

        target_source = self._pick_target_source(event)
        if not target_source:
            yield event.plain_result(
                "提示：/{} 指令需要带图发送，或者 @你要处理的人。".format(command.name)
            )
            return

        yield event.plain_result(command.message)
        job_dir = self._make_job_dir(command.name)
        input_path = job_dir / "target.png"
        output_base = job_dir / "result"
        output_path = output_base.with_suffix(".{}".format(command.output_ext))

        try:
            await self._save_image_source(target_source, input_path)
            script_path = self._resolve_script_path(command)

            args = [sys.executable, str(script_path)]
            if command.is_double:
                sender_path = job_dir / "sender.png"
                await self._save_image_source(
                    self._qq_avatar_source(event.get_sender_id()),
                    sender_path,
                )
                args.extend([str(sender_path), str(input_path), str(output_path)])
            else:
                args.extend([str(input_path), str(output_path)])

            args.extend(command.extra_args)
            script_result = await self._run_script(args)
            final_output = self._find_output_file(output_base, command.output_ext)

            if script_result.returncode != 0:
                logger.warning(
                    "表情生成失败: command=%s returncode=%s stdout=%s stderr=%s",
                    command.name,
                    script_result.returncode,
                    _clip_log_text(script_result.stdout),
                    _clip_log_text(script_result.stderr),
                )
                yield event.plain_result("生成失败了，请换张图再试，或者稍后重试。")
                return

            if final_output:
                yield self._build_image_result(event, final_output)
                return

            logger.warning("表情生成失败: command=%s no output file", command.name)
            yield event.plain_result("生成失败了：脚本没有输出图片。")
        except asyncio.TimeoutError:
            yield event.plain_result("生成超时了，请换张图再试，或者稍后重试。")
        except (httpx.HTTPError, FileNotFoundError, ValueError, binascii.Error) as exc:
            logger.warning("表情生成准备失败: command=%s error=%s", command.name, exc)
            yield event.plain_result("图片读取失败了，请换张图再试。")
        except Exception:
            logger.exception("表情插件逻辑出错: command=%s", command.name)
            yield event.plain_result("插件处理时遇到错误，请稍后再试。")
        finally:
            self._remove_path(job_dir)


class MemeArsenal(MemeStudioRuntime):
    pass


def _make_astrbot_command_handler(command_name: str, index: int):
    async def generated_command_handler(self: MemeStudioRuntime, event: AstrMessageEvent):
        command = self._commands_by_name().get(command_name)
        if command is None:
            return

        async for result in self._handle(event, command):
            yield result

    generated_command_handler.__name__ = "meme_command_{}".format(
        index,
    )
    generated_command_handler.__qualname__ = "MemeArsenal.{}".format(
        generated_command_handler.__name__,
    )
    return filter.command(command_name)(generated_command_handler)


def _install_astrbot_command_handlers() -> None:
    for index, command in enumerate(all_meme_commands(), start=1):
        handler = _make_astrbot_command_handler(command.name, index)
        setattr(MemeArsenal, handler.__name__, handler)


_install_astrbot_command_handlers()
