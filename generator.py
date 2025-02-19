from PIL import Image, ImageDraw, ImageFont
import textwrap
import random
import os
from google_fonts_python import GoogleFonts
import tempfile

# Configuration
IMG_WIDTH, IMG_HEIGHT = 1080, 720  # Image size
FONT_NAME = "Roboto"  # Choose any Google Font name
TEXT_COLOR = "white"
NUM_LINES = 4  # Max number of lines
MARGIN = 50  # Space around the text

# Initialize Google Fonts
google_fonts = GoogleFonts()

# Example quotes
quotes = [
    "The only way to do great work is to love what you do.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "In the middle of every difficulty lies opportunity."
]

# Ensure output directory exists
os.makedirs("output_images", exist_ok=True)

def generate_background():
    """Generates a random background color."""
    return (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

def get_optimal_font_size(draw, text, font_path, max_width, max_height):
    """Finds the largest font size that keeps text within bounds."""
    font_size = 100  # Start with a large font
    while font_size > 10:  # Prevent too small text
        font = ImageFont.truetype(font_path, font_size)
        wrapped_text = textwrap.fill(text, width=30)  # Adjust line width as needed
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if text_width <= max_width and text_height <= max_height:
            return font, wrapped_text
        font_size -= 2  # Reduce font size iteratively
    
    return ImageFont.truetype(font_path, 20), text  # Default to small font if needed

def get_font_path(font_name):
    """Downloads and returns the path to the specified Google Font."""
    # Download the font to a temporary file
    temp_dir = tempfile.gettempdir()
    font_path = google_fonts.download(font_name, temp_dir)
    return font_path

# Update FONT_PATH to use Google Font
FONT_PATH = get_font_path(FONT_NAME)

def create_image(quote, index):
    """Creates and saves an image with a centered quote."""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), generate_background())
    draw = ImageDraw.Draw(img)

    # Get optimal font size
    font, wrapped_text = get_optimal_font_size(draw, quote, FONT_PATH, IMG_WIDTH - 2*MARGIN, IMG_HEIGHT - 2*MARGIN)

    # Get text dimensions
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate centered position
    x = (IMG_WIDTH - text_width) // 2
    y = (IMG_HEIGHT - text_height) // 2

    # Draw text
    draw.text((x, y), wrapped_text, fill=TEXT_COLOR, font=font)

    # Save image
    img.save(f"output_images/quote_{index}.png")

# Generate images
for i, quote in enumerate(quotes):
    create_image(quote, i)

print("Quote images generated successfully!")
