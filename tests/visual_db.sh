#!/bin/bash

# ScyWeb Visualization Utility
# Converts .ppm databases to .png for visual analysis

DIR="vines_images"
OUT_DIR="visual_audits"
mkdir -p "$OUT_DIR"

# Colors
G='\033[0;32m'
B='\033[1m'
NC='\033[0m'

echo -e "${B}SCYWEB VISUALIZATION ENGINE${NC}"
echo "--------------------------------------------------------"

# Check for ImageMagick
if ! command -v convert &> /dev/null && ! command -v magick &> /dev/null; then
    echo "Error: ImageMagick is not installed. Install with 'sudo apt install imagemagick'."
    exit 1
fi

IMG_CMD=$(command -v magick || command -v convert)

for ppm in "$DIR"/*.ppm; do
    [ -e "$ppm" ] || continue
    filename=$(basename "$ppm" .ppm)
    echo -n "Converting $filename to PNG... "
    
    # We use -scale to keep the pixels sharp (no blurring/interpolation)
    # This allows the user to see the exact locations of the SQL "noise"
    $IMG_CMD "$ppm" -quality 100 "$OUT_DIR/${filename}.png"
    
    echo -e "${G}DONE${NC}"
done

echo "--------------------------------------------------------"
echo -e "${B}Visual audits saved to: /${OUT_DIR}${NC}"
ls -lh "$OUT_DIR"