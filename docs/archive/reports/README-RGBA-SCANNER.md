# RGBA Values Scanner and Replacer

A comprehensive tool to find and replace hardcoded `rgba()` values with design tokens in CSS files.

## Features

- 🔍 **Smart Scanning**: Finds all `rgba()` patterns in CSS files outside of token definitions
- 🎯 **Color Matching**: Matches rgba values to existing color variables in your design system
- 💡 **Intelligent Suggestions**: Suggests opacity modifiers or creates new semantic colors
- 🔄 **Batch Replacement**: Safely replaces multiple rgba values at once
- 💾 **Automatic Backup**: Creates timestamped backups before making changes
- 📊 **Detailed Reporting**: Generates comprehensive reports before and after replacement
- ↩️ **Rollback Support**: Easy rollback functionality
- 🎨 **Design System Aware**: Understands your existing color token structure

## Installation

The tool is already set up in your project. No additional installation required.

## Usage

### Quick Start

```bash
# Scan for rgba values (dry run)
npm run rgba:scan

# Auto-replace high-confidence matches
npm run rgba:replace

# Interactive replacement mode
npm run rgba:interactive

# Show help
npm run rgba:help
```

### Manual Usage

```bash
# Dry run with verbose output
node scan-rgba-values.js --dry-run --verbose

# Auto-replace high confidence matches (> 80% confidence)
node scan-rgba-values.js --auto-replace

# Interactive mode - review each replacement
node scan-rgba-values.js --interactive
```

## How It Works

### 1. Color Token Parsing
The tool automatically parses your design system's color tokens from:
- `web/static/css/design-system/01-tokens/colors.css`

It extracts:
- Hex color values and their variable names
- Existing RGB variables (e.g., `--accent-600-rgb: 79, 70, 229`)

### 2. RGBA Pattern Detection
Scans all CSS files except token definition files for patterns like:
- `rgba(99, 102, 241, 0.1)`
- `rgba(255, 255, 255, 0.8)`
- `rgba(0, 0, 0, 0.5)`

### 3. Color Matching
For each rgba pattern found:
- **Exact Match**: Direct RGB match with existing tokens
- **Close Match**: Color distance algorithm finds near matches
- **Confidence Score**: Calculates how confident the match is (0-100%)

### 4. Replacement Suggestions
Based on the match and alpha value:
- **Fully Opaque (α=1.0)**: Use color token directly
- **With Existing RGB Variable**: Use `rgba(var(--token-rgb), α)`
- **New Semantic Color**: Suggest creating new variables like `--primary-light`

### 5. Safe Application
- Creates timestamped backups before modification
- Applies replacements in reverse order to maintain file positions
- Provides rollback instructions

## Example Output

### Scan Report
```
📊 RGBA Scan Report
==================================================
Files scanned: 32
RGBA patterns found: 102
Potential replacements: 85
Unique RGBA patterns: 45

🎨 Unique RGBA patterns found:
  rgba(99, 102, 241, 0.1)
  rgba(255, 255, 255, 0.8)
  rgba(0, 0, 0, 0.5)
  ...

🔄 Replacement suggestions:

  --accent-500:
    web/static/css/components/cards.css:42
      rgba(99, 102, 241, 0.1) → rgba(var(--accent-600-rgb), 0.1)
      💡 Using existing RGB variable for transparency
      🎯 Confidence: 100.0%
```

### Suggested New Variables
```
💡 Suggested RGB variables to add to colors.css:
  --accent-500-rgb: 99, 102, 241;
  --success-500-rgb: 16, 185, 129;
  --error-500-rgb: 239, 68, 68;
```

## Configuration

The tool is pre-configured for the Linker project structure:
- **CSS Directory**: `web/static/css`
- **Tokens Directory**: `web/static/css/design-system/01-tokens`
- **Backup Directory**: `rgba-backup`

### Common Alpha Values
The tool recognizes semantic meanings for common alpha values:
- `0.05` → `subtle`
- `0.1` → `light`
- `0.15` → `soft`
- `0.2` → `medium`
- `0.3` → `emphasis`
- `0.4` → `strong`
- `0.5` → `semi`

## Safety Features

### Backup System
Every replacement operation creates a timestamped backup:
```
💾 Creating backup at: rgba-backup/backup-2024-01-15T10-30-45-123Z
```

### Rollback Instructions
After replacement, the tool provides exact rollback commands:
```
💡 To rollback: cp -r rgba-backup/backup-2024-01-15T10-30-45-123Z/* web/static/css/
```

### Confidence Thresholds
- **Auto-replace**: Only applies changes with > 80% confidence
- **Interactive mode**: Shows confidence for each replacement
- **Manual review**: All suggestions include reasoning

## Integration with Design System

### Current Token Structure
The tool understands your existing color system:
```css
/* Base colors */
--accent-600: #4f46e5;
--success-600: #059669;
--error-600: #dc2626;

/* RGB variables (for transparency) */
--accent-600-rgb: 79, 70, 229;
--success-600-rgb: 5, 150, 105;
--error-600-rgb: 220, 38, 38;
```

### Recommended Additions
Based on scan results, the tool suggests adding RGB variables:
```css
/* Add these to colors.css for better rgba support */
--accent-500-rgb: 99, 102, 241;
--warning-500-rgb: 245, 158, 11;
```

## Best Practices

### Before Running
1. **Commit your changes**: Ensure your CSS is committed to git
2. **Run dry-run first**: Always start with `--dry-run --verbose`
3. **Review suggestions**: Check the detailed report

### During Replacement
1. **Start with interactive**: Use `--interactive` for first-time runs
2. **High confidence first**: Use `--auto-replace` for obvious matches
3. **Review low confidence**: Manually review matches < 80% confidence

### After Replacement
1. **Test thoroughly**: Check your application visually
2. **Keep backups**: Don't delete backup folders immediately
3. **Update design system**: Add suggested RGB variables to your tokens

## Troubleshooting

### No Matches Found
- Ensure color tokens are properly defined in `colors.css`
- Check that rgba patterns use exact RGB values from your tokens
- Verify file paths are correct

### Low Confidence Matches
- Colors might be slightly different from your tokens
- Consider updating your design system to include these colors
- Use interactive mode to review manually

### Backup/Rollback Issues
- Ensure you have write permissions to the backup directory
- Check disk space before running large replacements
- Use absolute paths for rollback commands

## Advanced Usage

### Custom Paths
```bash
# Scan specific directory
node scan-rgba-values.js --dry-run --verbose ./custom/css/path

# Custom backup location
BACKUP_DIR=./my-backups node scan-rgba-values.js --auto-replace
```

### Report Analysis
The tool generates `rgba-scan-report.json` with detailed data:
- All found patterns with locations
- Confidence scores and reasoning
- Suggested improvements to design system

## Examples

### Full Workflow
```bash
# 1. Initial scan
npm run rgba:scan

# 2. Review report
cat rgba-scan-report.json

# 3. Interactive replacement
npm run rgba:interactive

# 4. Test and verify
# ... test your application ...

# 5. Rollback if needed (example)
cp -r rgba-backup/backup-2024-01-15T10-30-45-123Z/* web/static/css/
```

### Integration with Build Process
Add to your CI/CD:
```bash
# Check for new hardcoded rgba values
node scan-rgba-values.js --dry-run || exit 1
```

## Contributing

To extend the tool:
1. **Color matching algorithm**: Modify the `findColorMatch()` method
2. **Alpha semantics**: Update the `commonAlphas` mapping
3. **Report format**: Customize the `generateReport()` method

## Support

For issues or questions:
1. Check the detailed report output
2. Review backup files if replacements fail
3. Use `--verbose` mode for debugging
4. Ensure your design system structure matches expectations

---

**Note**: This tool is specifically designed for the Linker project's CSS structure but can be adapted for other design systems with similar token organization.