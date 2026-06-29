#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "舔屏"


def generate_prpr(image_path: str, output_path: str):
    """生成舔屏效果图片并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    frame_path = img_dir / "0.png"
    if not frame_path.exists():
        raise FileNotFoundError(f"缺失底图: {frame_path}")

    try:
        # 加载背景模板
        frame = BuildImage.open(frame_path)

        # 处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA")

        # 透视变换参数（左上，右上，右下，左下）
        processed_img = user_img.resize((330, 330), keep_ratio=True).perspective(
            ((0, 19), (236, 0), (287, 264), (66, 351))
        )

        # 合成最终图片 (将用户图片垫在底图下方)
        final_img = frame.copy().paste(processed_img, (56, 284), below=True)

        # 💡 核心修复：必须加上 .image 提取底层 PIL 对象，才能安全调用原生的 save 方法
        final_img.image.save(output_path, format="PNG")
        return True

    except Exception as e:
        raise RuntimeError(f"图片处理失败: {str(e)}")


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出图片路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_prpr(str(input_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)