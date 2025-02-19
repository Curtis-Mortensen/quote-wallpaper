import os
import sqlite3
import requests
from PIL import Image, ImageDraw, ImageFont
import re


def get_all_quotes(db_path='quotes.db'):
    # Check if the database exists; if not, create it and add a sample quote
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT
            )
        """)
        sample_quote = "Achievement Unlocked! Keep pushing your limits."
        cur.execute("INSERT INTO quotes (quote) VALUES (?)", (sample_quote,))
        conn.commit()
        conn.close()
    
    # Connect and fetch all quotes
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, quote FROM quotes")
    quotes = cur.fetchall()
    conn.close()
    
    print("Processing quotes:")
    for quote_id, quote_text in quotes:
        print(f"ID: {quote_id}, Quote: {quote_text}")
    
    return quotes


def download_font(font_path, font_url):
    if not os.path.exists(font_path):
        response = requests.get(font_url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            with open(font_path, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception(f"Failed to download font from {font_url}")
    return font_path


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = ''
    for word in words:
        test_line = word if current_line == '' else current_line + ' ' + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]  # width is right - left
        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def create_gradient_background(width, height, center_color='#222222', edge_color='#111111'):
    # Create a new image with RGB color
    image = Image.new('RGB', (width, height))
    
    # Convert hex colors to RGB tuples
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    center_rgb = hex_to_rgb(center_color)
    edge_rgb = hex_to_rgb(edge_color)
    
    # Calculate center point
    center_x = width // 2
    center_y = height // 2
    
    # Calculate max distance (from center to corner)
    max_distance = ((width//2)**2 + (height//2)**2)**0.5
    
    # Create radial gradient
    for y in range(height):
        for x in range(width):
            # Calculate distance from center (normalized to 0-1)
            distance = ((x - center_x)**2 + (y - center_y)**2)**0.5 / max_distance
            # Smooth out the gradient
            distance = distance ** 0.5  # This makes the gradient more pronounced in the center
            # Create gradient color
            color = tuple(int(center_rgb[i] + (edge_rgb[i] - center_rgb[i]) * distance) for i in range(3))
            image.putpixel((x, y), color)
    
    return image


def create_plaque_gradient(width, height, center_color='#804020', edge_color='#703018'):
    # Create a new image with RGB color
    image = Image.new('RGB', (width, height))
    
    # Convert hex colors to RGB tuples
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    center_rgb = hex_to_rgb(center_color)
    edge_rgb = hex_to_rgb(edge_color)
    
    # Calculate center point
    center_x = width // 2
    center_y = height // 2
    
    # Calculate max distance (from center to corner)
    max_distance = ((width//2)**2 + (height//2)**2)**0.5
    
    # Create radial gradient
    for y in range(height):
        for x in range(width):
            # Calculate distance from center (normalized to 0-1)
            distance = ((x - center_x)**2 + (y - center_y)**2)**0.5 / max_distance
            # Make the gradient more subtle
            distance = distance ** 2  # This makes the gradient change more gradually
            # Limit the maximum effect of the gradient
            distance = min(distance * 0.3, 0.3)  # This keeps the gradient subtle
            # Create gradient color
            color = tuple(int(center_rgb[i] + (edge_rgb[i] - center_rgb[i]) * distance) for i in range(3))
            image.putpixel((x, y), color)
    
    return image


def choose_font_for_text(text, draw, max_width, max_height, font_path, max_font_size=300, min_font_size=10, max_lines=7):
    # Start with a more conservative max font size
    current_max = min(max_font_size, int(max_height / (7 * 1.5)))  # More conservative initial size
    
    def check_text_fit(font_size):
        font = ImageFont.truetype(font_path, font_size)
        lines = wrap_text(text, font, max_width, draw)
        
        # Debug print for text fitting
        print(f"\nTrying font size: {font_size}")
        print(f"Number of lines: {len(lines)}")
        
        if len(lines) > max_lines:
            print(f"Too many lines: {len(lines)} > {max_lines}")
            return None, None, None, None
            
        # Calculate line metrics
        line_height = draw.textbbox((0, 0), "Test", font=font)[3] - draw.textbbox((0, 0), "Test", font=font)[1]
        line_spacing = line_height * 0.3
        
        # Calculate total height including spacing
        total_height = (len(lines) - 1) * (line_height + line_spacing) + line_height
        
        # Check if any line is too wide or total height is too tall
        max_line_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            max_line_width = max(max_line_width, line_width)
            if line_width > max_width:
                print(f"Line too wide: {line_width} > {max_width}")
                print(f"Problem line: {line}")
                return None, None, None, None
                
        if total_height > max_height:
            print(f"Total height too large: {total_height} > {max_height}")
            return None, None, None, None
            
        print(f"Success - Font size {font_size} fits:")
        print(f"Max line width: {max_line_width}/{max_width}")
        print(f"Total height: {total_height}/{max_height}")
        return font, lines, total_height, line_spacing
    
    # Binary search for the largest working font size
    low, high = min_font_size, current_max
    best_result = None
    
    while low <= high:
        mid = (low + high) // 2
        result = check_text_fit(mid)
        
        if result[0] is not None:
            best_result = result
            low = mid + 1
        else:
            high = mid - 1
    
    if best_result is None:
        # If nothing worked, use minimum size
        return check_text_fit(min_font_size)
    
    # Final size check
    font, lines, height, spacing = best_result
    print(f"\nFinal font size selected: {font.size}")
    print("Final text layout:")
    for line in lines:
        print(f"Line: {line}")
    
    return best_result


def main():
    # Get all quotes from the database
    quotes = get_all_quotes('quotes.db')
    
    # Process each quote
    for quote_id, quote_text in quotes:
        print(f"\nProcessing quote {quote_id}...")
        
        # New image dimensions
        width, height = 2560, 1440
        img = create_gradient_background(width, height, center_color='#1A1A1A', edge_color='#0A0A0A')
        draw = ImageDraw.Draw(img)

        # Define plaque dimensions with margins (plaque takes up less of the image)
        plaque_x = width * 0.15  # 15% from left edge
        plaque_y = height * 0.15  # 15% from top edge
        plaque_width = width * 0.7  # 70% of width
        plaque_height = height * 0.7  # 70% of height

        edge_offset = 30  # Offset for 3D layering effect

        # Draw dark shadow (bottom layer)
        draw.rectangle([
            plaque_x + edge_offset, plaque_y + edge_offset,
            plaque_x + plaque_width, plaque_y + plaque_height
        ], fill='#402020')

        # Draw lighter highlight (top layer)
        draw.rectangle([
            plaque_x, plaque_y,
            plaque_x + plaque_width - edge_offset, plaque_y + plaque_height - edge_offset
        ], fill='#503020')

        # Create and paste the plaque gradient
        plaque_inset = 15
        plaque_face_width = int(plaque_width - 2 * plaque_inset)
        plaque_face_height = int(plaque_height - 2 * plaque_inset)
        plaque_gradient = create_plaque_gradient(plaque_face_width, plaque_face_height)
        img.paste(plaque_gradient, (int(plaque_x + plaque_inset), int(plaque_y + plaque_inset)))

        # Define text area inside the plaque with consistent margins
        horizontal_margin = int(plaque_width * 0.08)  # 8% of plaque width
        top_margin = int(plaque_height * 0.06)  # 6% of plaque height for top
        bottom_margin = int(plaque_height * 0.08)  # 8% of plaque height for bottom

        # Define text area coordinates
        text_area_x = plaque_x + horizontal_margin + plaque_inset
        text_area_y = plaque_y + top_margin + plaque_inset
        text_area_width = plaque_width - 2 * (horizontal_margin + plaque_inset)
        text_area_height = plaque_height - (top_margin + bottom_margin + 2 * plaque_inset)

        # Download Merriweather font from Google Fonts if not already present
        font_filename = 'Merriweather-Regular.ttf'
        font_url = 'https://fonts.googleapis.com/css2?family=Merriweather&display=swap'
        
        # First get the CSS
        response = requests.get(font_url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            css = response.text
            # Extract the actual font URL from the CSS
            font_url_match = re.search(r'src: url\((.*?)\)', css)
            if font_url_match:
                font_url = font_url_match.group(1)
            else:
                raise Exception("Could not find font URL in Google Fonts CSS")
        else:
            raise Exception("Failed to fetch Google Fonts CSS")

        download_font(font_filename, font_url)

        # Choose the largest font size that allows the quote to fit in the text area
        font, lines, total_text_height, line_spacing = choose_font_for_text(
            quote_text, draw, text_area_width, text_area_height, 
            font_filename, max_font_size=300, min_font_size=10, max_lines=7
        )

        # Calculate starting y position to vertically center the text
        # Bias towards top by reducing the centering offset
        centering_bias = 0.8  # This will move text up by reducing the empty space above
        current_y = text_area_y + (text_area_height - total_text_height) * centering_bias / 2
        text_color = '#FFE866'  # Lighter gold for the text

        # Draw each line centered in the text area
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            x = text_area_x + (text_area_width - line_width) / 2
            draw.text((x, current_y), line, font=font, fill=text_color)
            current_y += line_height + line_spacing

        # Save the final plaque image with quote ID in filename
        output_path = f'plaque_quote_{quote_id}.png'
        img.save(output_path)
        print(f'Saved plaque image: {output_path}')


if __name__ == '__main__':
    main()
