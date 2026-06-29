#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "膜拜"


def generate_worship(image_path: str, output_path: str):
    """生成膜拜动画GIF并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA")

        # 💡 保留原版精妙的透视变换坐标
        perspective_points = ((0, -30), (135, 17), (135, 145), (0, 140))

        # 处理图片为 150x150 并应用透视
        processed_img = user_img.square().resize((150, 150))
        processed_img = processed_img.perspective(perspective_points)

        # 动态检测帧数保护
        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        # 生成动画帧
        frames: List[IMG] = []
        for i in range(frame_count):
            frame_path = img_dir / f"{i}.png"
            frame = BuildImage.open(frame_path)
            # 保持原始合成方式：用户图片垫在背景小人下方
            frame.paste(processed_img, below=True)
            frames.append(frame.image)

        # 💡 核心修复：原生保存为 GIF，替代 save_gif
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=40,  # 0.04秒 = 40毫秒
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

            generate_worship(str(input_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)