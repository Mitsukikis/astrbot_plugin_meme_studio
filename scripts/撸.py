#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image


def true_crop(img, target_size=(540, 477)):
    """真正的居中裁剪，切除多余部分"""
    img_w, img_h = img.size
    target_w, target_h = target_size

    # 计算需要的最小缩放比例
    scale = max(target_w / img_w, target_h / img_h)

    # 缩放图片
    scaled = img.resize((int(img_w * scale), int(img_h * scale)), Image.Resampling.LANCZOS)

    # 计算裁剪区域
    left = (scaled.width - target_w) // 2
    top = (scaled.height - target_h) // 2
    return scaled.crop((left, top, left + target_w, top + target_h))


def process_image(input_path, output_path, mode):
    try:
        user_img = Image.open(input_path).convert("RGB")
    except Exception as e:
        raise RuntimeError(f"图片加载失败: {e}")

    # 统一目标尺寸
    TARGET_SIZE = (540, 477)

    # 💡 锁死默认选项：居中智能裁剪，防止人物拉伸变形
    resized_user = true_crop(user_img, TARGET_SIZE)

    # 根据传入参数选择模式目录
    mode_dir = "双手撸" if mode == '1' else "单手撸"

    # 获取当前所在目录 (scripts/)
    script_dir = Path(__file__).parent.resolve()
    # 💡 核心修改：向上跳一级，进入 data/撸/，然后再拼接上 mode_dir
    frame_dir = script_dir.parent / "data" / "撸" / mode_dir

    if not frame_dir.exists():
        raise FileNotFoundError(f"找不到文件夹: {frame_dir}")

    # 获取当前模式的8张图
    frame_files = [frame_dir / f"{i}.png" for i in range(8)]

    frames = []
    for frame_file in frame_files:
        if not frame_file.exists():
            raise FileNotFoundError(f"缺失帧文件: {frame_file.name}")

        # 抖动帧适配目标尺寸
        jerk_frame = Image.open(frame_file).convert("RGBA").resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        # 合成图片（底部居中）
        composite = Image.new("RGBA", TARGET_SIZE)
        composite.paste(resized_user, (0, 0))
        composite.alpha_composite(jerk_frame, (0, TARGET_SIZE[1] - jerk_frame.height))

        frames.append(composite.convert("RGB"))

    # 💡 使用原生方案保存 GIF，替代 imageio
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,  # 0.1秒 = 100毫秒
        loop=0,
        disposal=2
    )


if __name__ == "__main__":
    try:
        # 💡 核心修复：兼容 2 个参数的情况
        if len(sys.argv) >= 3:
            input_file = sys.argv[1]
            output_file = sys.argv[2]
            
            # 💡 如果 main.py 传了模式就用，没传就默认 '1'（双手撸）
            mode = sys.argv[3] if len(sys.argv) >= 4 else '1'

            if not Path(input_file).exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            process_image(input_file, output_file, mode)
            print(f"动图已生成: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)