from PIL import Image, ImageDraw
import os

def generate_icon(size, filename, color="#4f8ef7"):
    # Create a base image with the primary color background
    img = Image.new('RGBA', (size, size), color=color)
    draw = ImageDraw.Draw(img)
    
    # Draw a stylized "D" or a simple chart-like shape
    # Let's draw a simple bar chart icon
    padding = size // 5
    bar_width = (size - 2 * padding) // 4
    
    # Bar 1
    draw.rectangle([padding + 0, size - padding - (size // 3), padding + bar_width - 10, size - padding], fill="white")
    # Bar 2
    draw.rectangle([padding + bar_width, size - padding - (size // 2), padding + 2 * bar_width - 10, size - padding], fill="white")
    # Bar 3
    draw.rectangle([padding + 2 * bar_width, size - padding - (size // 1.5), padding + 3 * bar_width - 10, size - padding], fill="white")
    
    img.save(filename)
    print(f"Generated {filename} ({size}x{size})")

if __name__ == "__main__":
    os.makedirs("assets/icons", exist_ok=True)
    generate_icon(192, "assets/icons/icon-192.png")
    generate_icon(512, "assets/icons/icon-512.png")
    # Also a maskable icon (padding required)
    generate_icon(512, "assets/icons/icon-maskable.png")
