#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

INPUT="report.md"
OUTPUT="report.pdf"

if [ ! -f "$INPUT" ]; then
    echo "Error: $INPUT not found"
    exit 1
fi

echo "Building PDF from $INPUT..."

pandoc "$INPUT" \
    -o "$OUTPUT" \
    --standalone \
    --highlight-style=tango \
    --pdf-engine=lualatex \
    --pdf-engine-opt="--shell-escape" \
    --lua-filter="filters/diagram.lua" \
    --include-in-header=header.tex \
    --extract-media=media \
    -V "titlepage=true" \
    -V "title=COMP2003 Project Report" \
    -V "author=Mervin Manuel, David Williams, Oscar Kennedy, Harry McDevitt" \
    -V "date=$(date +%B\ %Y)" \
    -V "papersize=a4" \
    -V "geometry=margin=2.5cm" \
    -V "toc-title=Table of Contents" \
    -V "mainfont=Times New Roman" \
    -V "mainfontfallback=NotoColorEmoji:mode=harf" \
    -V "sansfont=Arial" \
    -V "monofont=Latin Modern Mono" \
    -V "monofontfallback=NotoColorEmoji:mode=harf" \
    -V "documentclass=report" \
    -V "hyperrefoptions=colorlinks=true" \
    -V "linkcolor=blue" \
    -V "urlcolor=blue"

# Cleanup media directory
rm -rf media

if [ -f "$OUTPUT" ]; then
    echo "PDF generated successfully: $OUTPUT"
else
    echo "Error: PDF generation failed"
    exit 1
fi
