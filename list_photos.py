import os
import sys

base_dir = r"C:\Users\truji\OneDrive\PERSONAL\Imágenes\Fotos productos\Atlanctic Pet"

for root, dirs, files in os.walk(base_dir):
    for name in files:
        rel_path = os.path.relpath(os.path.join(root, name), base_dir)
        print(rel_path)
