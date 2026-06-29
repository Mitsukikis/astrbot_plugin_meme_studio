#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


class DOGenerator:
    def __init__(self, fps=20):
        self.self_locs = [(116, -8), (109, 3), (130, -10)]
        self.user_locs = [(2, 177), (12, 172), (6, 158)]
        self.fps = fps
        # 直接获取当前脚本的绝对路径
        script_dir = Path(__file__).parent.resolve()
        self.images_dir = str(script_dir.parent / "data" / "撅")

    def circle_mask(self, size):
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        return mask

    def process_head(self, img, size, rotation):
        img = img.convert("RGBA")
        img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)
        mask = self.circle_mask(size)
        img.putalpha(mask)
        return img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))

    def generate_frame(self, i, self_img, user_img):
        template_file = os.path.join(self.images_dir, f"{i}.png")
        if not os.path.exists(template_file):
            raise FileNotFoundError(f"找不到底图: {template_file}")

        base = Image.open(template_file).convert('RGBA')
        bg = Image.new("RGB", base.size, (255, 255, 255))
        bg.paste(base, mask=base)
        base = bg

        self_head = self.process_head(self_img, (122, 122), -15)
        user_head = self.process_head(user_img, (112, 112), 90)

        base = base.convert("RGBA")
        base.alpha_composite(self_head, dest=self.self_locs[i])
        base.alpha_composite(user_head, dest=self.user_locs[i])
        return base.convert('RGB')

    def generate_gif(self, self_path, user_path, output_path):
        if not os.path.exists(self.images_dir):
            raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {self.images_dir}")

        self_img = Image.open(self_path).convert("RGBA")
        user_img = Image.open(user_path).convert("RGBA")
        frames = []
        for i in range(3):
            frame = self.generate_frame(i, self_img.copy(), user_img.copy())
            frames.append(frame)

        duration = 1 / self.fps
        frames[0].save(
            output_path, save_all=True, append_images=frames[1:],
            duration=int(duration * 1000), loop=0, optimize=True, disposal=2
        )
        return True


if __name__ == "__main__":
    try:
        # 接收三个参数：主动方路径，被动方路径，输出路径
        if len(sys.argv) >= 4:
            sender = sys.argv[1]
            target = sys.argv[2]
            output = sys.argv[3]

            if not os.path.exists(sender) or not os.path.exists(target):
                print("错误: 输入的图片文件不存在！", file=sys.stderr)
                sys.exit(1)

            gen = DOGenerator()
            gen.generate_gif(sender, target, output)
            print(f"生成成功: {output}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"脚本处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)