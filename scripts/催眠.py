#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "催眠"


def generate_saimin(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    # 加载输入图片
    try:
        input_img = BuildImage.open(image_path)
    except Exception as e:
        raise RuntimeError(f"无法读取图片文件: {e}")

    # 💡 动态获取帧数，免疫缺帧报错
    frame_count = 0
    while (img_dir / f"{frame_count}.png").exists():
        frame_count += 1

    if frame_count == 0:
        raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到，请确保有 0.png 等文件！")

    frame_files = [img_dir / f"{i}.png" for i in range(frame_count)]

    # 准备动画参数
    app_w, app_h = BuildImage.open(frame_files[0]).size
    img_w, img_h = input_img.size
    ratio = 1

    # 计算调整尺寸
    if img_w > img_h:
        frame_h = round(app_h * ratio)
        frame_w = round(frame_h * img_w / img_h)
    else:
        frame_w = round(app_w * ratio)
        frame_h = round(frame_w * img_h / img_w)

    # 生成所有帧
    frames = []
    for frame_file in frame_files:
        # 调整输入图片
        resized = input_img.resize((frame_w, frame_h), keep_ratio=True).convert("RGBA")

        # 创建透明画布
        frame = Image.new("RGBA", (app_w, app_h))

        # 合成图片 (底层是输入图，顶层是催眠波纹特效)
        frame.paste(resized.image, (0, app_h - frame_h), resized.image)
        overlay = BuildImage.open(frame_file).convert("RGBA")
        frame.paste(overlay.image, (0, 0), overlay.image)

        frames.append(frame)

    # 💡 直接原生保存，抛弃所有依赖
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=30,  # 原版为每帧30毫秒，旋转非常快
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
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_saimin(str(input_file), str(output_file))
            print(f"生成成功！保存路径：{output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)