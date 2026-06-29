#!/usr/bin/env python3
import sys
from pathlib import Path

from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "顶"


def generate_play(image_path: str, output_path: str):
    """生成顶玩动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    # 确保38张图片齐全
    if not all((img_dir / f"{i}.png").exists() for i in range(38)):
        raise FileNotFoundError("缺少帧图片资源，请确保images目录包含0.png到37.png")

    # 加载用户图片
    user_img = BuildImage.open(image_path).convert("RGBA").square()

    # 各帧位置参数 (x, y, w, h)
    locs = [
        (180, 60, 100, 100), (184, 75, 100, 100), (183, 98, 100, 100),
        (179, 118, 110, 100), (156, 194, 150, 48), (178, 136, 122, 69),
        (175, 66, 122, 85), (170, 42, 130, 96), (175, 34, 118, 95),
        (179, 35, 110, 93), (180, 54, 102, 93), (183, 58, 97, 92),
        (174, 35, 120, 94), (179, 35, 109, 93), (181, 54, 101, 92),
        (182, 59, 98, 92), (183, 71, 90, 96), (180, 131, 92, 101)
    ]

    # 加载原始帧
    raw_frames = [BuildImage.open(img_dir / f"{i}.png") for i in range(38)]

    # 生成合成帧
    img_frames = []
    for i in range(len(locs)):
        frame = raw_frames[i].copy()
        x, y, w, h = locs[i]
        frame.paste(user_img.resize((w, h)), (x, y), below=True)
        img_frames.append(frame)

    # 组合最终帧序列（这套逻辑绝妙，原封不动保留）
    frames = (
            img_frames[0:12] * 2  # 重复前12帧两次
            + img_frames[0:8]  # 添加前8帧
            + img_frames[12:18]  # 添加中间帧
            + raw_frames[18:38]  # 添加剩余原始帧
    )

    # 直接保存输出到文件
    pil_frames = [frame.image for frame in frames]
    pil_frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=pil_frames[1:],
        duration=60,  # 0.06秒 = 60毫秒
        loop=0,
        disposal=2
    )
    return True


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出GIF路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误：文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_play(str(input_file), str(output_file))
            print(f"生成成功：{output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败：{str(e)}", file=sys.stderr)
        sys.exit(1)