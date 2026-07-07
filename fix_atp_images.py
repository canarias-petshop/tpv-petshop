import os
import glob
from PIL import Image

web_img_dir = r"D:\clon vs mode\web-petshop\public\images\productos"
atp_images = glob.glob(os.path.join(web_img_dir, "ATP-*.jpg"))

fixed = 0
for img_path in atp_images:
    try:
        with Image.open(img_path) as img:
            # Check if it needs conversion (it's actually webp or has transparency)
            if img.format != 'JPEG':
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    # Save as real JPEG, overwriting the file
                    background.save(img_path, "JPEG", quality=95)
                else:
                    # Just convert to RGB and save
                    img.convert('RGB').save(img_path, "JPEG", quality=95)
                fixed += 1
    except Exception as e:
        print(f"Error processing {img_path}: {e}")

print(f"Imágenes de Atlantic Pet convertidas a JPG real: {fixed}")
