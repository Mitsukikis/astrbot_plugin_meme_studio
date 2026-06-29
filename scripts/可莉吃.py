#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "可莉吃"


def generate_klee_eat(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片为正方形并调整尺寸
        user_img = BuildImage.open(image_path)
        processed_img = user_img.convert("RGBA").square().resize((83, 83))

        # 使用你提供的精确位置参数 (x, y)
        locs = [
            (0, 174), (0, 174), (0, 174), (0, 174), (0, 174),
            (12, 160), (19, 152), (23, 148), (26, 145), (32, 140),
            (37, 136), (42, 131), (49, 127), (70, 126), (88, 128),
            (-30, 210), (-19, 207), (-14, 200), (-10, 188), (-7, 179),
            (-3, 170), (-3, 175), (-1, 174), (0, 174), (0, 174),
            (0, 174), (0, 174), (0, 174), (0, 174), (0, 174), (0, 174)
        ]

        # 动态检测文件夹里的真实图片数量
        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        # 生成动画帧
        frames = []
        for i in range(frame_count):
            frame = BuildImage.open(img_dir / f"{i}.png")
            # 坐标防越界保护：如果帧数超出坐标预设，就一直用最后一个坐标
            coord = locs[i] if i < len(locs) else locs[-1]
            frame.paste(processed_img, coord, below=True)
            frames.append(frame.image)

        # 原生方法保存为 GIF
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=100,  # 使用原代码的 0.1秒 = 100毫秒
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

            generate_klee_eat(str(input_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)