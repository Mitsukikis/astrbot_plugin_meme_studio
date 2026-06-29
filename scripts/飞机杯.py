#!/usr/bin/env python3
import sys
import cv2
import numpy as np
from PIL import Image
from pathlib import Path

# 原Rust代码中的params参数
params = [
    ([(0, 6), (205, 0), (213, 157), (8, 171)], (117, 59)),
    ([(0, 6), (205, 0), (213, 157), (8, 171)], (117, 59)),
    ([(0, 6), (205, 0), (213, 157), (8, 171)], (117, 59)),
    ([(0, 7), (204, 0), (213, 157), (8, 172)], (118, 58)),
    ([(0, 6), (207, 0), (213, 158), (8, 173)], (119, 57)),
    ([(0, 6), (207, 0), (213, 158), (8, 173)], (119, 57)),
    ([(0, 6), (207, 0), (213, 158), (8, 173)], (119, 57)),
    ([(0, 6), (205, 0), (212, 157), (7, 171)], (121, 58)),
    ([(0, 6), (205, 0), (212, 157), (7, 171)], (121, 58)),
    ([(0, 6), (206, 0), (212, 158), (8, 172)], (121, 56)),
    ([(0, 6), (206, 0), (212, 158), (8, 172)], (121, 56)),
    ([(0, 6), (207, 0), (214, 157), (10, 171)], (121, 55)),
    ([(0, 7), (201, 0), (218, 154), (13, 169)], (121, 49)),
    ([(0, 7), (195, 0), (219, 147), (18, 162)], (118, 50)),
    ([(0, 4), (196, 0), (223, 133), (18, 143)], (114, 54)),
    ([(0, 0), (192, 1), (219, 121), (17, 124)], (115, 58)),
    ([(0, 0), (188, 5), (220, 110), (20, 107)], (112, 61)),
    ([(0, 0), (185, 15), (217, 86), (26, 73)], (108, 72)),
    ([(0, 0), (182, 19), (234, 67), (34, 44)], (102, 88)),
    ([(0, 0), (175, 25), (224, 55), (22, 23)], (111, 105)),
    ([(0, 0), (167, 29), (209, 49), (13, 14)], (121, 110)),
    ([(0, 0), (144, 27), (195, 46), (8, 8)], (135, 110)),
    ([(0, 0), (177, 36), (206, 59), (13, 18)], (129, 93)),
    ([(0, 0), (180, 38), (211, 69), (16, 25)], (126, 83)),
    ([(0, 0), (181, 28), (220, 70), (26, 39)], (119, 82)),
    ([(0, 0), (180, 17), (227, 65), (27, 45)], (115, 89)),
    ([(0, 0), (181, 15), (230, 63), (33, 46)], (110, 95)),
    ([(0, 0), (184, 24), (228, 73), (27, 47)], (91, 102)),
    ([(0, 0), (189, 8), (208, 73), (0, 66)], (83, 94)),
    ([(19, 0), (202, 25), (204, 85), (0, 58)], (63, 82)),
    ([(12, 0), (196, 18), (205, 70), (0, 50)], (70, 87)),
    ([(4, 0), (189, 17), (205, 74), (0, 53)], (82, 79)),
    ([(0, 0), (184, 18), (205, 72), (1, 51)], (91, 74)),
    ([(0, 0), (183, 17), (206, 69), (4, 52)], (92, 73)),
]


def resize_to_cover(img, target_size):
    """按cover模式调整图像尺寸"""
    target_w, target_h = target_size
    img_w, img_h = img.size

    ratio = max(target_w / img_w, target_h / img_h)
    new_size = (int(img_w * ratio), int(img_h * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)

    # 居中裁剪
    left = (new_size[0] - target_w) / 2
    top = (new_size[1] - target_h) / 2
    right = left + target_w
    bottom = top + target_h
    return img.crop((left, top, right, bottom))


def apply_perspective(pil_img, dest_points):
    """应用透视变换"""
    # 转换PIL图像为OpenCV格式（RGBA）
    img = np.array(pil_img.convert('RGBA'))
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)

    h, w = img.shape[:2]
    src_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst_pts = np.float32(dest_points)

    # 计算变换矩阵并应用
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(
        img, matrix, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255, 0)
    )

    # 转换回PIL图像
    return Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGRA2RGBA))


def generate_gif(input_path, output_path):
    # 获取脚本当前所在目录 (scripts/)
    script_dir = Path(__file__).parent.resolve()
    # 💡 核心修改：向上跳一级，进入 data/飞机杯
    frame_dir = script_dir.parent / "data" / "飞机杯"

    if not frame_dir.exists():
        raise FileNotFoundError(f"错误：缺少背景图目录 {frame_dir}")

    # 加载并处理输入图像
    main_img = Image.open(input_path)
    main_img = resize_to_cover(main_img, (210, 170))

    frames = []
    for i in range(34):
        # 加载背景帧
        frame_path = frame_dir / f"{i:02d}.png"
        if not frame_path.exists():
            raise FileNotFoundError(f"错误：缺少背景图 {frame_path}")
        frame = Image.open(frame_path).convert("RGBA")

        # 获取当前参数
        points, pos = params[i]

        # 应用透视变换
        warped = apply_perspective(main_img, points)

        # 合成图像
        composite = Image.new("RGBA", frame.size, (255, 255, 255, 255))
        composite.paste(warped, pos, warped)  # 粘贴处理后的图像
        composite.paste(frame, (0, 0), frame)  # 叠加背景帧

        # 转换为RGB并收集帧
        frames.append(composite.convert("RGB"))

    # 保存GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
        optimize=True
    )


if __name__ == "__main__":
    try:
        # 接收外部传入的输入路径和输出路径
        if len(sys.argv) >= 3:
            input_file = sys.argv[1]
            output_file = sys.argv[2]

            if not Path(input_file).exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_gif(input_file, output_file)
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)