#!/usr/bin/env python3
import sys
from pathlib import Path
from io import BytesIO

from pil_utils import BuildImage
from _gif_utils import FrameAlignPolicy, make_gif_or_combined_gif

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "汤姆嘲笑"


def generate_tom_tease(image_path: str) -> BytesIO:
    """生成汤姆嘲笑动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    img = BuildImage.open(image_path)

    # 💡 核心修复：把 list[BuildImage] 改成单张 BuildImage，提前解决报错隐患
    def frame_maker(i: int):
        def make_frame(base_img: BuildImage) -> BuildImage:
            # 处理用户图片
            processed_img = base_img.convert("RGBA").resize((400, 350), keep_ratio=True)
            processed_img = processed_img.perspective(((0, 100), (290, 0), (290, 370), (0, 335)))

            # 加载当前帧背景
            bg = BuildImage.open(img_dir / f"{i}.png")

            # 合成帧
            frame = BuildImage.new("RGBA", bg.size, "white")
            frame.paste(bg).paste(processed_img, (258, -12), below=True)
            return frame

        return make_frame

    # 生成GIF数据
    return make_gif_or_combined_gif(
        img,  # 💡 核心修复：直接传 img 对象，而不是 [img] 列表
        frame_maker,
        11,
        0.2,
        FrameAlignPolicy.extend_first
    )


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出GIF路径
        if len(sys.argv) >= 3:
            input_path = Path(sys.argv[1])
            output_path = Path(sys.argv[2])

            if not input_path.exists():
                print(f"错误: 文件 {input_path} 不存在！", file=sys.stderr)
                sys.exit(1)

            # 生成并保存GIF
            gif_io = generate_tom_tease(str(input_path))
            with open(output_path, "wb") as f:
                f.write(gif_io.getvalue())

            print(f"成功生成: {output_path}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"生成失败: {str(e)}", file=sys.stderr)
        sys.exit(1)
