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

# Create temp Lua filter to handle emojis
LUA_FILTER=$(mktemp --suffix=.lua)
cat > "$LUA_FILTER" << 'EOF'
-- Lua filter to convert common emojis to text equivalents
local emoji_map = {
  ["✅"] = "[PASS]",
  ["❌"] = "[FAIL]",
  ["⚠️"] = "[WARNING]",
  ["📝"] = "[NOTE]",
  ["🎮"] = "[GAME]",
  ["💡"] = "[IDEA]"
}

function Str(elem)
  if emoji_map[elem.text] then
    return pandoc.Str(emoji_map[elem.text])
  end
  return elem
end

function Code(elem)
  for emoji, replacement in pairs(emoji_map) do
    elem.text = string.gsub(elem.text, emoji, replacement)
  end
  return elem
end

function CodeBlock(elem)
  for emoji, replacement in pairs(emoji_map) do
    elem.text = string.gsub(elem.text, emoji, replacement)
  end
  return elem
end
EOF

pandoc "$INPUT" \
    -o "$OUTPUT" \
    --standalone \
    --toc \
    --toc-depth=2 \
    --highlight-style=tango \
    --pdf-engine=lualatex \
    --pdf-engine-opt="--shell-escape" \
    --lua-filter="filters/diagram.lua" \
    --lua-filter="$LUA_FILTER" \
    --extract-media=media \
    -V "titlepage=true" \
    -V "title=COMP2003 Project Report" \
    -V "author=Mervin Manuel, David Williams, Oscar Kennedy, Harry McDevitt" \
    -V "date=$(date +%B\ %Y)" \
    -V "papersize=a4" \
    -V "geometry=margin=2.5cm" \
    -V "toc-title=Table of Contents" \
    -V "mainfont=Times New Roman" \
    -V "sansfont=Arial" \
    -V "documentclass=report" \
    -V "hyperrefoptions=colorlinks=true" \
    -V "linkcolor=blue" \
    -V "urlcolor=blue"

# Cleanup temp file and media directory
rm -f "$LUA_FILTER"
rm -rf media

if [ -f "$OUTPUT" ]; then
    echo "PDF generated successfully: $OUTPUT"
else
    echo "Error: PDF generation failed"
    exit 1
fi
