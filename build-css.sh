#!/bin/bash

# CSS Build Script
# 建構和壓縮 CSS 文件

echo "🎨 Starting CSS build process..."

# Create minified directory
mkdir -p web/static/css/dist

# Combine all design system CSS into one file
echo "📦 Combining design system files..."
cat web/static/css/design-system/index.css \
    web/static/css/design-system/01-tokens/*.css \
    web/static/css/design-system/02-base/*.css \
    web/static/css/design-system/03-components/*.css \
    web/static/css/design-system/04-layouts/*.css \
    > web/static/css/dist/design-system.combined.css

# Minify the combined file
echo "🗜️ Minifying CSS..."
npx postcss web/static/css/dist/design-system.combined.css \
    -o web/static/css/dist/design-system.min.css

# Create production-ready files for pages
echo "📄 Processing page CSS files..."
for file in web/static/css/pages/*.css; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .css)
        npx postcss "$file" -o "web/static/css/dist/$filename.min.css"
    fi
done

# Calculate size reduction
original_size=$(du -sh web/static/css/design-system | cut -f1)
minified_size=$(du -sh web/static/css/dist/design-system.min.css | cut -f1)

echo "✅ Build complete!"
echo "📊 Original size: $original_size"
echo "📊 Minified size: $minified_size"
echo "📍 Output directory: web/static/css/dist/"

# Optional: Generate CSS stats
echo ""
echo "📈 CSS Statistics:"
echo "-------------------"
echo "Total CSS files: $(find web/static/css -name "*.css" -not -path "*/dist/*" -not -path "*/backup-phase4/*" | wc -l)"
echo "Total lines: $(find web/static/css -name "*.css" -not -path "*/dist/*" -not -path "*/backup-phase4/*" -exec wc -l {} + | tail -1 | awk '{print $1}')"
echo "Minified files: $(ls -1 web/static/css/dist/*.min.css 2>/dev/null | wc -l)"