#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "科目三"


def generate_subject3(image_path: str, output_path: str):
    # 确保有85帧图片资源
    if not img_dir.exists() or not all((img_dir / f"{i}.png").exists() for i in range(85)):
        raise FileNotFoundError(f"缺少帧图片资源，请确保 {img_dir} 目录存在且包含 0.png 到 84.png 全部 85 张图！")

    # 加载用户头像并处理为圆形
    user_head = BuildImage.open(image_path).convert("RGBA")
    user_head = user_head.circle().resize((120, 120))

    # 坐标数据
    # fmt: off
    locs = [
        (60, 71), (61, 73), (62, 71), (66, 70), (75, 69),
        (87, 74), (87, 74), (85, 76), (79, 73), (76, 71),
        (68, 69), (66, 73), (66, 74), (66, 74), (66, 71),
        (76, 65), (80, 65), (91, 73), (91, 77), (91, 75),
        (86, 71), (83, 69), (78, 68), (73, 67), (68, 74),
        (68, 77), (71, 73), (81, 68), (88, 69), (96, 73),
        (98, 78), (97, 79), (93, 76), (85, 71), (80, 66),
        (71, 69), (69, 74), (68, 77), (68, 77), (80, 70),
        (91, 68), (95, 71), (98, 78), (97, 79), (95, 78),
        (86, 69), (77, 64), (71, 69), (71, 73), (69, 73),
        (73, 67), (78, 65), (88, 65), (91, 72), (94, 77),
        (91, 74), (89, 70), (83, 63), (75, 60), (69, 67),
        (67, 74), (68, 73), (76, 64), (77, 60), (84, 62),
        (92, 68), (92, 73), (90, 69), (86, 66), (80, 61),
        (69, 63), (65, 67), (60, 76), (62, 73), (66, 68),
        (75, 62), (77, 62), (85, 69), (86, 73), (85, 75),
        (78, 70), (74, 67), (67, 67), (65, 72), (65, 79),
    ]
    # fmt: on

    # 生成所有帧
    frames = []
    for frame_index in range(85):
        frame = BuildImage.open(img_dir / f"{frame_index}.png")
        frame.paste(user_head, locs[frame_index], alpha=True)
        frames.append(frame.image)

    # 💡 核心修复：直接使用原生保存方法处理巨量帧数，duration 80ms (约 0.08s)
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
        disposal=2
    )
    print(f"科目三动画已生成：{output_path}")


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出GIF路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误：文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_subject3(str(input_file), str(output_file))
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"生成失败：{str(e)}", file=sys.stderr)
        sys.exit(1)