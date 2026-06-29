from enum import Enum
from io import BytesIO
from typing import Callable, List, Sequence, Union

from PIL import Image as PILImage
from PIL import ImageSequence
from pil_utils import BuildImage


class FrameAlignPolicy(Enum):
    extend_first = "extend_first"
    extend_loop = "extend_loop"


Maker = Callable[[BuildImage], BuildImage]


def _to_pil_image(image: Union[BuildImage, PILImage.Image]) -> PILImage.Image:
    if isinstance(image, BuildImage):
        return image.image
    return image


def _to_build_image(image: Union[BuildImage, PILImage.Image]) -> BuildImage:
    if isinstance(image, BuildImage):
        return image
    return BuildImage(image.convert("RGBA"))


def _source_frames(image: Union[BuildImage, PILImage.Image]) -> List[BuildImage]:
    pil_image = _to_pil_image(image)
    if getattr(pil_image, "is_animated", False):
        return [
            BuildImage(frame.convert("RGBA").copy())
            for frame in ImageSequence.Iterator(pil_image)
        ]
    return [_to_build_image(image)]


def _pick_frame(
    frames: Sequence[BuildImage],
    index: int,
    policy: FrameAlignPolicy,
) -> BuildImage:
    if not frames:
        raise ValueError("至少需要一帧输入图片")

    if policy is FrameAlignPolicy.extend_loop:
        return frames[index % len(frames)]

    if index < len(frames):
        return frames[index]
    return frames[0]


def _save_gif(frames: Sequence[PILImage.Image], duration_ms: int) -> BytesIO:
    if not frames:
        raise ValueError("至少需要一帧输出图片")

    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=list(frames[1:]),
        duration=duration_ms,
        loop=0,
        disposal=2,
    )
    output.seek(0)
    return output


def make_gif_or_combined_gif(
    image: Union[BuildImage, PILImage.Image],
    frame_maker: Callable[[int], Maker],
    frame_count: int,
    duration: float,
    align_policy: FrameAlignPolicy,
) -> BytesIO:
    source_frames = _source_frames(image)
    rendered_frames = []

    for index in range(frame_count):
        source = _pick_frame(source_frames, index, align_policy)
        rendered = frame_maker(index)(source)
        rendered_frames.append(_to_pil_image(rendered).convert("RGBA"))

    return _save_gif(rendered_frames, max(1, int(duration * 1000)))


def make_jpg_or_gif(images: Sequence[BuildImage], maker: Callable[[List[BuildImage]], BuildImage]):
    if not images:
        raise ValueError("至少需要一张输入图片")

    source_frames = _source_frames(images[0])
    if len(source_frames) == 1:
        return maker(list(images))

    rendered_frames = []
    for source in source_frames:
        current_images = [source]
        current_images.extend(images[1:])
        rendered = maker(current_images)
        rendered_frames.append(_to_pil_image(rendered).convert("RGBA"))

    duration_ms = _to_pil_image(images[0]).info.get("duration", 80)
    return _save_gif(rendered_frames, duration_ms)
