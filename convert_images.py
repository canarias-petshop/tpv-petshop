import glob
import os
from PIL import Image

image_dir = r"D:\clon vs mode\web-petshop\public\images\productos"
files = glob.glob(os.path.join(image_dir, "LE-*"))

converted = 0
for f in files:
    ext = os.path.splitext(f)[1].lower()
    if ext in [".png", ".webp", ".jpeg"]:
        new_path = os.path.splitext(f)[0] + ".jpg"
        try:
            # Open and convert to RGB (removing alpha channel for PNG)
            with Image.open(f) as img:
                rgb_im = img.convert('RGB')
                rgb_im.save(new_path, "JPEG")
            # Remove original file if it's not already .jpg
            if f != new_path:
                os.remove(f)
                converted += 1
        except Exception as e:
            print(f"Error converting {f}: {e}")

print(f"Convertidas {converted} imágenes a .jpg")
