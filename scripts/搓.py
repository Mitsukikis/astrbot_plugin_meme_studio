#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "搓"


def generate_twist(image_path: str, output_path: str):
    """生成搓动动画GIF并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理图片：转为正方形并缩放至 78x78
        img = BuildImage.open(image_path).convert("RGBA")
        img = img.square().resize((78, 78))

        # 帧位置及旋转参数 (x, y, 旋转角度)
        locs = [
            (25, 66, 0), (25, 66, 60), (23, 68, 120),
            (20, 69, 180), (22, 68, 240)
        ]

        frames: List[IMG] = []
        for i in range(5):
            frame_file = img_dir / f"{i}.png"
            if not frame_file.exists():
                raise FileNotFoundError(f"缺失帧图片: {frame_file.name}")

            frame = BuildImage.open(frame_file)
            x, y, angle = locs[i]

            # 旋转并粘贴图片，below=True 表示垫在手部素材下方
            rotated_img = img.rotate(angle)
            frame.paste(rotated_img, (x, y), below=True)
            frames.append(frame.image)

        # 💡 核心优化：直接利用原生方法保存为 GIF，抛弃外部依赖
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=100,  # 0.1秒 = 100毫秒
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

            generate_twist(str(input_file), str(output_file))
            print(f"成功生成: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)