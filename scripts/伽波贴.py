#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "伽波贴"


def capoo_rub(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理图片尺寸和形状
        img = BuildImage.open(image_path).convert("RGBA").square().resize((180, 180))

        frames: List[IMG] = []
        # 各帧对应的 w(宽), h(高), x(X坐标), y(Y坐标)
        locs = [
            (178, 184, 78, 260),
            (178, 174, 84, 269),
            (178, 174, 84, 269),
            (178, 178, 84, 264),
        ]

        for i in range(4):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第{i}帧素材图：{frame_path}")

            frame = BuildImage.open(frame_path)
            w, h, x, y = locs[i]
            # 合成图片，置于底层
            frame.paste(img.resize((w, h)), (x, y), below=True)
            frames.append(frame.image)

        # 💡 原生保存为 GIF
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=100,  # 原版的 0.1秒 = 100毫秒
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

            capoo_rub(str(input_file), str(output_file))
            print(f"生成完成！文件已保存至：{output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)