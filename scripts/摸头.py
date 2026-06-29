#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "摸头"


def generate_petpet(image_path: str, output_path: str):
    """生成摸头动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片为正方形
        user_img = BuildImage.open(image_path).convert("RGBA").square()

        # 各帧图片形变和位置参数 (x, y, w, h)
        locs = [
            (14, 20, 98, 98),
            (12, 33, 101, 85),
            (8, 40, 110, 76),
            (10, 33, 102, 84),
            (12, 20, 98, 98),
        ]

        # 生成动画帧
        frames = []
        for i in range(5):
            # 加载背景手部动作帧
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第{i}帧背景图: {frame_path}")

            frame = BuildImage.open(frame_path)
            x, y, w, h = locs[i]

            # 处理图片形变并合成（注意是被手压在下面，所以 below=True）
            resized_img = user_img.resize((w, h))
            frame.paste(resized_img, (x, y), below=True)
            frames.append(frame.image)

        # 原生保存为 GIF
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=60,  # 0.06秒 = 60毫秒
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

            generate_petpet(str(input_path), str(output_path))
            print(f"生成成功: {output_path}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)