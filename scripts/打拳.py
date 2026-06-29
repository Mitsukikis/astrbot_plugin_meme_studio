#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "打拳"


def generate_punch(image_path: str, output_path: str):
    """生成打拳动画GIF并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片：强制转为正方形并调整尺寸
        user_img = BuildImage.open(image_path).convert("RGBA")
        user_img = user_img.square().resize((260, 260))

        # 各帧偏移参数 (x, y) - 完美保留你的原版精妙逻辑
        position_offsets = [
            (-50, 20), (-40, 10), (-30, 0), (-20, -10), (-10, -10), (0, 0),
            (10, 10), (20, 20), (10, 10), (0, 0), (-10, -10), (10, 0), (-30, 10)
        ]

        frames = []
        for frame_index in range(13):
            # 加载拳头素材
            fist_path = img_dir / f"{frame_index}.png"
            if not fist_path.exists():
                raise FileNotFoundError(f"缺失第{frame_index}帧拳头素材: {fist_path}")

            fist_img = BuildImage.open(fist_path)

            # 创建新画布 (白色背景)
            frame = BuildImage.new("RGBA", fist_img.size, "white")

            # 计算粘贴位置
            x_offset, y_offset = position_offsets[frame_index]
            final_y = y_offset - 15  # 固定垂直偏移调整

            # 合成用户图片和拳头
            frame.paste(user_img, (x_offset, final_y), alpha=True)
            frame.paste(fist_img, alpha=True)

            frames.append(frame.image)

        # 💡 核心优化：利用原生方法保存为 GIF，彻底丢弃外部依赖
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=30,  # 原版的 0.03秒 = 30毫秒，非常快的连打速度
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

            generate_punch(str(input_path), str(output_path))
            print(f"生成成功: {output_path}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)