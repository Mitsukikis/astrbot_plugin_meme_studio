#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "垃圾桶"


def generate_garbage(image_path: str, output_path: str):
    """生成垃圾动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA").square().resize((79, 79))

        # 定义位置参数
        locs = (
                [] + [(39, 40)] * 3 + [(39, 30)] * 2 + [(39, 32)] * 10
                + [(39, 30), (39, 27), (39, 32), (37, 49), (37, 64),
                   (37, 67), (37, 67), (39, 69), (37, 70), (37, 70)]
        )

        # 生成动画帧
        frames = []
        for i in range(25):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第 {i} 帧背景图: {frame_path}")

            frame = BuildImage.open(frame_path)
            frame.paste(user_img, locs[i], below=True)
            frames.append(frame.image)

        # 💡 使用原生方法保存为 GIF，弃用 meme_generator 依赖
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
            input_path = Path(sys.argv[1])
            output_path = Path(sys.argv[2])

            if not input_path.exists():
                print(f"错误: 文件 {input_path} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_garbage(str(input_path), str(output_path))
            print(f"生成成功: {output_path}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)