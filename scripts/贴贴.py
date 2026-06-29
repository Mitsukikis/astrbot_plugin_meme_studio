#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "贴贴"

def generate_rub(self_path: str, target_path: str, output_path: str):
    """生成贴贴动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理双方头像为圆形
        self_head = BuildImage.open(self_path).convert("RGBA").circle()
        user_head = BuildImage.open(target_path).convert("RGBA").circle()

        user_locations = [
            (39, 91, 75, 75), (49, 101, 75, 75), (67, 98, 75, 75),
            (55, 86, 75, 75), (61, 109, 75, 75), (65, 101, 75, 75)
        ]
        self_locations = [
            (102, 95, 70, 80, 0), (108, 60, 50, 100, 0), (97, 18, 65, 95, 0),
            (65, 5, 75, 75, -20), (95, 57, 100, 55, -70), (109, 107, 65, 75, 0)
        ]

        # 动态检测帧数并加以保护
        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        limit = min(frame_count, len(user_locations), len(self_locations))

        frames = []
        for frame_index in range(limit):
            frame = BuildImage.open(img_dir / f"{frame_index}.png")

            # 粘贴被动方图片
            u_x, u_y, u_w, u_h = user_locations[frame_index]
            frame.paste(user_head.resize((u_w, u_h)), (u_x, u_y), alpha=True)

            # 粘贴主动方图片 (包含旋转逻辑)
            s_x, s_y, s_w, s_h, s_angle = self_locations[frame_index]
            rotated_self = self_head.resize((s_w, s_h)).rotate(s_angle, expand=True)
            frame.paste(rotated_self, (s_x, s_y), alpha=True)

            frames.append(frame.image)

        # 💡 原生保存，抛弃一切依赖
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
        # 接收外部传入的三个参数：主动方图片，被动方图片，输出GIF路径
        if len(sys.argv) >= 4:
            self_file = Path(sys.argv[1])
            target_file = Path(sys.argv[2])
            output_file = Path(sys.argv[3])

            if not self_file.exists() or not target_file.exists():
                print("错误: 输入的图片文件不存在！", file=sys.stderr)
                sys.exit(1)

            generate_rub(str(self_file), str(target_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)