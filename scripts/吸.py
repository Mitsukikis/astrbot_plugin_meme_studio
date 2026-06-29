#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "吸"


def generate_suck(image_path: str, output_path: str):
    """生成吸入动画GIF并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片为正方形
        user_img = BuildImage.open(image_path).convert("RGBA").square()

        # 💡 保留原版精妙的 12 帧位置参数 (x, y, w, h)
        locs = [
            (82, 100, 130, 119), (82, 94, 126, 125), (82, 120, 128, 99), (81, 164, 132, 55),
            (79, 163, 132, 55), (82, 140, 127, 79), (83, 152, 125, 67), (75, 157, 140, 62),
            (72, 165, 144, 54), (80, 132, 128, 87), (81, 127, 127, 92), (79, 111, 132, 108)
        ]

        frames: List[IMG] = []
        for i in range(12):
            # 加载背景帧
            bg_path = img_dir / f"{i}.png"
            if not bg_path.exists():
                raise FileNotFoundError(f"缺失素材图片: {bg_path.name}")
            bg = BuildImage.open(bg_path)

            # 建立纯白底板并合成
            frame = BuildImage.new("RGBA", bg.size, "white")
            x, y, w, h = locs[i]

            # 合成顺序：底层头像 -> 顶层素材
            frame.paste(user_img.resize((w, h)), (x, y), alpha=True)
            frame.paste(bg, alpha=True)
            frames.append(frame.image)

        # 💡 核心修复：原生保存为 GIF，替代 save_gif
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=80,  # 0.08秒 = 80毫秒
            loop=0,
            disposal=2
        )
        return True

    except Exception as e:
        raise RuntimeError(f"生成失败: {str(e)}")


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出GIF路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_suck(str(input_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)