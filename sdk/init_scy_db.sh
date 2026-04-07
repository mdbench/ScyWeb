#!/bin/bash

DB_NAME="scy_database.ppm"
echo "🚀 Initializing ScyWeb Database: $DB_NAME"

# 1. Create a GUARANTEED 15-byte header
# Header: 'P6 4000 4000 255' (14 chars) + '\n' (1 char) = 15 bytes
# We use -n to prevent printf from adding its own newline
printf "P6 4000 4000 255\n" > "$DB_NAME"

# 2. Force truncate the header to exactly 15 bytes 
# (This kills any \r\n or trailing space issues)
head -c 15 "$DB_NAME" > "${DB_NAME}.tmp" && mv "${DB_NAME}.tmp" "$DB_NAME"

# 3. Append exactly 48,000,000 bytes of zeros
# bs=1 is slower but universally accurate across all dd versions
dd if=/dev/zero bs=1000000 count=48 >> "$DB_NAME" 2>/dev/null

# 4. Final Validation
FILE_SIZE=$(wc -c < "$DB_NAME")
EXPECTED_SIZE=48000015

if [ "$FILE_SIZE" -eq "$EXPECTED_SIZE" ]; then
    echo "✅ Success! Database is ready."
    echo "📏 Size: $FILE_SIZE bytes (Bit-Perfect 15 + 48M)"
else
    echo "❌ Error: File size mismatch."
    echo "   Expected: $EXPECTED_SIZE"
    echo "   Actual:   $FILE_SIZE"
    echo "   Difference: $((FILE_SIZE - EXPECTED_SIZE)) bytes"
    
    # Debug: Check the header size specifically
    HEADER_SIZE=$(head -c 20 "$DB_NAME" | wc -c)
    echo "   Check: First 15 bytes check resulted in $HEADER_SIZE bytes."
    exit 1
fi