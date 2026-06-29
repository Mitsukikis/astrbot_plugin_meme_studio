#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List

from PIL.Image import Image as IMG
from pil_utils import BuildImage


script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "抱抱"


def generate_hug(self_path: str, user_path: str, output_path: str):
    """生成抱抱动图 GIF。"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到素材目录: {img_dir}")

    try:
        # 发送者在下方拥抱，对方在上方被抱。
        self_head = BuildImage.open(self_path).convert("RGBA").circle().resize((120, 120))
        user_head = BuildImage.open(user_path).convert("RGBA").circle().resize((105, 105))

        user_locs = [
            (108, 15), (107, 14), (104, 16), (102, 14), (104, 15),
            (108, 15), (108, 15), (103, 16), (102, 15), (104, 14),
        ]
        self_locs = [
            (78, 120), (115, 130), (0, 0), (110, 100), (80, 100),
            (75, 115), (105, 127), (0, 0), (110, 98), (80, 105),
        ]
        rotate_num = [-48, -18, 0, 38, 31, -43, -22, 0, 34, 35]

        frames: List[IMG] = []
        for i in range(10):
            frame = BuildImage.open(img_dir / f"{i}.png")
            frame.paste(user_head, user_locs[i], below=True)

            rotated_self = self_head.rotate(rotate_num[i], expand=True)
            frame.paste(rotated_self, self_locs[i], below=True)
            frames.append(frame.image)

        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=50,
            loop=0,
            disposal=2,
        )
        return True
    except Exception as exc:
        raise RuntimeError(f"生成失败: {exc}") from exc


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 4:
            sender_p = sys.argv[1]
            target_p = sys.argv[2]
            out_p = sys.argv[3]

            generate_hug(sender_p, target_p, out_p)
            sys.exit(0)

        print("缺少参数", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"执行错误: {exc}", file=sys.stderr)
        sys.exit(1)
