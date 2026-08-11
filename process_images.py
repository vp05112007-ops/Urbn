import os
import glob
from rembg import remove
from PIL import Image, ImageEnhance, ImageOps

src_dir = "static/img/customizer/"

mapping = {
    "hoodie_black": "hoodie-Black",
    "hoodie_white": "hoodie-White",
    "hoodie_gray": "hoodie-Gray",
    "hoodie_red": "hoodie-Red",
    "sweatshirt_black": "sweatshirt-Black",
    "sweatshirt_white": "sweatshirt-White",
    "sweatshirt_gray": "sweatshirt-Gray",
    "sweatshirt_red": "sweatshirt-Red",
    "tshirt_black": "tshirt-Black",
    "tshirt_white": "tshirt-White",
    "tshirt_gray": "tshirt-Gray",
    "tshirt_red": "tshirt-Red",
    "jacket_black": "jacket-Black"
}

# 1. Remove backgrounds and rename
for file in glob.glob(src_dir + "*.png"):
    filename = os.path.basename(file)
    if "media" in filename:
        os.remove(file)
        continue
        
    prefix = ""
    for k, v in mapping.items():
        if filename.startswith(k):
            prefix = v
            break
            
    if not prefix:
        continue
        
    try:
        input_image = Image.open(file)
        output_image = remove(input_image)
        output_image.save(src_dir + prefix + ".webp", format="webp", quality=90)
        os.remove(file) # delete original
        print(f"Processed {prefix}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

# 2. Fake the missing jackets
try:
    jacket_black = Image.open(src_dir + "jacket-Black.webp").convert("RGBA")
    
    # White Jacket: Invert lightness, increase brightness
    r, g, b, a = jacket_black.split()
    rgb_image = Image.merge('RGB', (r,g,b))
    inverted = ImageOps.invert(rgb_image)
    enhancer = ImageEnhance.Brightness(inverted)
    white_jacket = enhancer.enhance(1.2)
    white_jacket.putalpha(a)
    white_jacket.save(src_dir + "jacket-White.webp", format="webp", quality=90)
    
    # Gray Jacket: Less brightness
    gray_jacket = enhancer.enhance(0.7)
    gray_jacket.putalpha(a)
    gray_jacket.save(src_dir + "jacket-Gray.webp", format="webp", quality=90)
    
    # Red Jacket: Colorize inverted
    red_jacket = ImageOps.colorize(ImageOps.grayscale(inverted), black="darkred", white="#ff6666")
    red_jacket.putalpha(a)
    red_jacket.save(src_dir + "jacket-Red.webp", format="webp", quality=90)
    print("Generated missing jackets")
except Exception as e:
    print("Error generating jackets:", e)

