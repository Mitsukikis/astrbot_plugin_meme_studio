#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "吃"


def generate_eat(image_path: str, output_path: str):
    """生成吃东西动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片
        user_img = BuildImage.open(image_path)
        processed_img = user_img.convert("RGBA").square().resize((34, 34))

        # 生成动画帧
        frames = []
        for i in range(3):
            # 加载背景帧
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第{i}帧背景图: {frame_path}")

            frame = BuildImage.open(frame_path)
            # 合成图片（固定位置）
            frame.paste(processed_img, (2, 38), below=True)
            frames.append(frame.image)

        # 💡 直接利用原生方法保存为 GIF，抛弃外部依赖库
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=50,  # 0.05秒 = 50毫秒
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

            generate_eat(str(input_path), str(output_path))
            print(f"生成成功: {output_path}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)