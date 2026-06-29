#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "拿捏"


def generate_tease(image_path: str, output_path: str):
    """生成拿捏动画GIF并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA").square()

        # 💡 精准保留你原代码中的 24 帧参数配置 (位置坐标, 透视点)
        frame_params = [
            ((21, 75), ((0, 0), (129, 3), (155, 123), (12, 142))),
            ((18, 73), ((0, 29), (128, 0), (149, 118), (30, 147))),
            ((22, 78), ((0, 37), (136, 1), (160, 97), (16, 152))),
            ((22, 58), ((0, 58), (169, 1), (194, 92), (24, 170))),
            ((43, 23), ((0, 114), (166, 17), (144, 185), (0, 137))),
            ((38, 26), ((0, 126), (180, 20), (161, 169), (0, 139))),
            ((37, 26), ((0, 131), (183, 21), (165, 166), (0, 140))),
            ((37, 26), ((0, 130), (183, 21), (165, 167), (0, 141))),
            ((37, 26), ((0, 131), (183, 21), (165, 166), (0, 140))),
            ((38, 26), ((0, 126), (180, 20), (161, 169), (0, 139))),
            ((43, 23), ((0, 114), (166, 17), (144, 185), (0, 137))),
            ((22, 58), ((0, 58), (169, 1), (194, 92), (24, 170))),
            ((22, 78), ((0, 37), (136, 1), (160, 97), (16, 152))),
            ((18, 73), ((0, 29), (128, 0), (149, 118), (30, 147))),
            ((21, 75), ((0, 0), (129, 3), (155, 123), (12, 142))),
            ((15, 78), ((-5, 0), (144, 0), (150, 122), (0, 119))),
            ((1, 87), ((0, 0), (157, 0), (157, 107), (0, 105))),
            ((1, 91), ((0, 0), (158, 0), (158, 103), (0, 101))),
            ((1, 91), ((0, 0), (158, 0), (158, 103), (0, 101))),
            ((2, 101), ((0, 0), (153, 0), (153, 122), (0, 120))),
            ((-18, 85), ((61, 0), (194, 15), (143, 146), (0, 133))),
            ((0, 66), ((88, 1), (173, 17), (123, 182), (0, 131))),
            ((0, 29), ((118, 3), (201, 48), (111, 220), (1, 168))),
            ((15, 78), ((-5, 0), (144, 0), (150, 122), (0, 119)))
        ]

        frames: List[IMG] = []
        for i in range(24):
            # 加载背景帧
            frame_file = img_dir / f"{i}.png"
            if not frame_file.exists():
                raise FileNotFoundError(f"缺失第{i}帧背景图")

            frame = BuildImage.open(frame_path if (frame_path := frame_file).exists() else frame_file)
            position, perspective_points = frame_params[i]

            # 应用透视变换并合成，below=True 表示垫在手部素材下方
            transformed_img = user_img.perspective(perspective_points)
            frame.paste(transformed_img, position, below=True)
            frames.append(frame.image)

        # 💡 原生保存为 GIF，抛弃 meme_generator
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

            generate_tease(str(input_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)