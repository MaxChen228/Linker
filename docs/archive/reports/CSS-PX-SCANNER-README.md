# CSS PX Value Scanner & Replacer

A comprehensive tool to scan and replace hardcoded px values with CSS variables in the Linker project. This tool helps maintain consistency in your design system by automatically suggesting and applying spacing token replacements.

## Features

- 🔍 **Smart Detection**: Finds hardcoded px values while excluding small border values (1-4px)
- 🎯 **Context Aware**: Skips border-related properties to avoid breaking border definitions
- 📊 **Detailed Reporting**: Generates comprehensive reports with file locations and suggestions
- 🔄 **Safe Replacement**: Creates backups before making any changes
- 🎨 **Token Mapping**: Maps px values to existing spacing tokens from your design system
- 🛡️ **Reversible**: All changes can be easily reverted using backups

## Quick Start

### Scan Only (Generate Report)
```bash
# Scan default CSS directory
node scan-px-values.js --scan

# Scan specific directory
node scan-px-values.js --scan ./web/static/css

# Using npm scripts
npm run scan
npm run scan:css
```

### Scan and Replace (with Backup)
```bash
# Replace in default directory
node scan-px-values.js --replace

# Replace in specific directory
node scan-px-values.js --replace ./web/static/css

# Using npm scripts
npm run replace
npm run replace:css
```

### Interactive Mode
```bash
# Full interactive experience
node scan-px-values.js --interactive

# Or using npm
npm run interactive
```

## How It Works

### 1. Detection Logic
The scanner identifies hardcoded px values but intelligently excludes:
- Border-related properties (`border`, `border-width`, `outline`, etc.)
- Small values typically used for borders (1px, 2px, 3px, 4px)
- CSS variable definitions (lines containing `--`)

### 2. Token Mapping
Based on your existing spacing system in `spacing.css`:
```css
--space-1: 4px     → 4px values
--space-2: 8px     → 8px values
--space-3: 12px    → 12px values
--space-4: 16px    → 16px values
--space-5: 20px    → 20px values
--space-6: 24px    → 24px values
--space-8: 32px    → 32px values
--space-10: 40px   → 40px values
--space-12: 48px   → 48px values
--space-15: 60px   → 60px values
--space-16: 64px   → 64px values
--space-20: 80px   → 80px values
--space-50: 400px  → 400px values
```

### 3. Safety Features
- **Automatic Backup**: Creates timestamped backups before any changes
- **Dry Run Mode**: Scan-only mode to preview changes
- **Specific Targeting**: Only replaces exact matches in appropriate contexts
- **Restoration Guide**: Clear instructions for reverting changes

## Report Format

The tool generates detailed reports showing:

```
📊 Summary:
   Total findings: 150
   Replaceable with tokens: 63
   Needs custom tokens: 87

✅ REPLACEABLE WITH EXISTING TOKENS:
20px → var(--space-5) (14 occurrences)
   📁 web/static/css/components/cards.css:42
      padding: 20px

⚠️ NEEDS CUSTOM TOKENS:
768px (17 occurrences)
   Suggested token: --space-768
   📁 web/static/css/responsive.css:15
      (max-width: 768px)
```

## Example Usage

### Scan and Preview Changes
```bash
$ node scan-px-values.js --scan
Found 33 CSS files to scan...

================================================================================
HARDCODED PX VALUES SCAN REPORT
================================================================================

📊 Summary:
   Total findings: 150
   Replaceable with tokens: 63
   Needs custom tokens: 87
```

### Apply Replacements
```bash
$ node scan-px-values.js --replace
Found 33 CSS files to scan...

📦 Creating backup in: css-backup-2024-12-01T10-30-00-000Z

🔄 Processing 15 files...
   ✅ web/static/css/components/cards.css - 8 replacements
   ✅ web/static/css/pages/practice.css - 12 replacements

🎉 Replacement complete!
   Total replacements: 63
   Backup location: css-backup-2024-12-01T10-30-00-000Z

💡 To restore from backup:
   cp -r "css-backup-2024-12-01T10-30-00-000Z"/* ./
```

## Configuration

### Custom Spacing Tokens
You can modify the `spacingTokens` object in the script to match your design system:

```javascript
this.spacingTokens = {
  '8px': 'var(--space-2)',
  '16px': 'var(--space-4)',
  '24px': 'var(--space-6)',
  // Add your custom mappings
};
```

### Excluded Properties
Customize which CSS properties to skip:

```javascript
this.excludedProperties = [
  'border',
  'border-width',
  'outline',
  // Add more properties to exclude
];
```

## Troubleshooting

### Restore from Backup
If you need to revert changes:
```bash
# Find your backup directory (shown in replacement output)
cp -r "css-backup-TIMESTAMP"/* ./
```

### Manual Token Creation
For values that need custom tokens, add them to your `spacing.css`:
```css
:root {
  --space-768: 768px;  /* For responsive breakpoints */
  --space-100: 100px;  /* For component sizing */
}
```

## Integration with Design System

This tool is designed to work seamlessly with the Linker design system:
- Uses existing spacing tokens from `web/static/css/design-system/01-tokens/spacing.css`
- Maintains consistency across all CSS files
- Supports responsive breakpoints and component sizing
- Compatible with the existing build process

## Advanced Usage

### Programmatic Usage
```javascript
const PxValueScanner = require('./scan-px-values.js');

const scanner = new PxValueScanner();
scanner.scanDirectory('./custom/path').then(() => {
  scanner.generateReport();
  // Access findings via scanner.findings
});
```

### Custom Filters
Extend the scanner for specific use cases:
```javascript
scanner.excludedValues.push('5px'); // Exclude additional values
scanner.excludedProperties.push('letter-spacing'); // Skip more properties
```

## Contributing

When adding new spacing tokens to the design system:
1. Update `spacing.css` with the new token
2. Update the `spacingTokens` mapping in this script
3. Re-run the scanner to apply the new mappings

## License

MIT License - Part of the Linker project.