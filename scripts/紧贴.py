#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "紧贴"


def generate_tightly(image_path: str, output_path: str):
    """ 生成紧贴动画GIF并保存 """
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片
        img = BuildImage.open(image_path).convert("RGBA")
        img = img.resize((640, 400), keep_ratio=True)

        # 20帧位置信息
        locs = [
            (39, 169, 267, 141), (40, 167, 264, 143), (38, 174, 270, 135),
            (40, 167, 264, 143), (38, 174, 270, 135), (40, 167, 264, 143),
            (38, 174, 270, 135), (40, 167, 264, 143), (38, 174, 270, 135),
            (28, 176, 293, 134), (5, 215, 333, 96), (10, 210, 321, 102),
            (3, 210, 330, 104), (4, 210, 328, 102), (4, 212, 328, 100),
            (4, 212, 328, 100), (4, 212, 328, 100), (4, 212, 328, 100),
            (4, 212, 328, 100), (29, 195, 285, 120)
        ]

        frames: List[IMG] = []
        for i in range(20):
            frame_file = img_dir / f"{i}.png"
            if not frame_file.exists():
                raise FileNotFoundError(f"缺失第{i}帧背景图")

            frame = BuildImage.open(frame_file)
            x, y, w, h = locs[i]
            # 合成图片，below=True 表示垫在背景层下方
            frame.paste(img.resize((w, h)), (x, y), below=True)
            frames.append(frame.image)

        # 💡 核心优化：直接原生保存，不再依赖 meme_generator
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

            generate_tightly(str(input_file), str(output_file))
            print(f"成功生成: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)