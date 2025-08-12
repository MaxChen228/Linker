#!/usr/bin/env node

/**
 * RGBA Values Scanner and Replacer
 * 
 * A comprehensive tool to find and replace hardcoded rgba values with design tokens.
 * Features:
 * - Scans CSS files for rgba() values outside of design-system/01-tokens/
 * - Matches rgba values to existing color variables
 * - Suggests opacity modifiers or creates new semantic colors
 * - Provides batch replacement capability with safety checks
 * - Includes rollback functionality and detailed reporting
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class RGBAScanner {
  constructor(options = {}) {
    this.cssDir = options.cssDir || 'web/static/css';
    this.tokensDir = 'web/static/css/design-system/01-tokens';
    this.backupDir = options.backupDir || 'rgba-backup';
    this.dryRun = options.dryRun || false;
    this.verbose = options.verbose || false;
    
    // Store color mappings and rgba patterns
    this.colorTokens = new Map();
    this.rgbaPatterns = new Set();
    this.replacements = [];
    this.report = {
      filesScanned: 0,
      rgbaFound: 0,
      potentialReplacements: 0,
      replacementsMade: 0,
      errors: []
    };
  }

  /**
   * Parse color tokens from the design system
   */
  parseColorTokens() {
    console.log('📖 Parsing color tokens from design system...');
    
    const colorsFile = path.join(this.tokensDir, 'colors.css');
    if (!fs.existsSync(colorsFile)) {
      throw new Error(`Colors file not found: ${colorsFile}`);
    }

    const content = fs.readFileSync(colorsFile, 'utf8');
    
    // Extract hex colors and their variable names
    const hexPattern = /--([^:]+):\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})/g;
    let match;
    
    while ((match = hexPattern.exec(content)) !== null) {
      const [, varName, hexValue] = match;
      const rgb = this.hexToRgb(hexValue);
      if (rgb) {
        this.colorTokens.set(`${rgb.r},${rgb.g},${rgb.b}`, {
          variable: varName,
          hex: hexValue,
          rgb: rgb
        });
      }
    }

    // Extract existing RGB variables (like --accent-600-rgb: 79, 70, 229)
    const rgbPattern = /--([^:]+)-rgb:\s*(\d+),\s*(\d+),\s*(\d+)/g;
    while ((match = rgbPattern.exec(content)) !== null) {
      const [, varName, r, g, b] = match;
      this.colorTokens.set(`${r},${g},${b}`, {
        variable: varName,
        rgb: { r: parseInt(r), g: parseInt(g), b: parseInt(b) },
        hasRgbVar: true
      });
    }

    console.log(`✅ Found ${this.colorTokens.size} color tokens`);
    
    if (this.verbose) {
      console.log('Color tokens:');
      for (const [rgb, token] of this.colorTokens) {
        console.log(`  ${rgb} -> --${token.variable}`);
      }
    }
  }

  /**
   * Convert hex to RGB
   */
  hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

  /**
   * Get all CSS files except token files
   */
  getCSSFiles() {
    const cssFiles = [];
    
    const walkDir = (dir) => {
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
          // Skip the tokens directory
          if (!fullPath.includes('01-tokens')) {
            walkDir(fullPath);
          }
        } else if (item.endsWith('.css')) {
          cssFiles.push(fullPath);
        }
      }
    };

    walkDir(this.cssDir);
    return cssFiles;
  }

  /**
   * Extract rgba patterns from CSS content
   */
  extractRgbaPatterns(content) {
    const rgbaRegex = /rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)/g;
    const patterns = [];
    let match;

    while ((match = rgbaRegex.exec(content)) !== null) {
      const [fullMatch, r, g, b, a] = match;
      patterns.push({
        fullMatch,
        r: parseInt(r),
        g: parseInt(g),
        b: parseInt(b),
        a: parseFloat(a),
        index: match.index
      });
    }

    return patterns;
  }

  /**
   * Find closest color match
   */
  findColorMatch(r, g, b) {
    const rgbKey = `${r},${g},${b}`;
    
    // Exact match
    if (this.colorTokens.has(rgbKey)) {
      return {
        type: 'exact',
        token: this.colorTokens.get(rgbKey),
        confidence: 1.0
      };
    }

    // Find closest match using color distance
    let closestMatch = null;
    let minDistance = Infinity;

    for (const [tokenRgb, token] of this.colorTokens) {
      const tokenRgbValues = tokenRgb.split(',').map(Number);
      const distance = Math.sqrt(
        Math.pow(r - tokenRgbValues[0], 2) +
        Math.pow(g - tokenRgbValues[1], 2) +
        Math.pow(b - tokenRgbValues[2], 2)
      );

      if (distance < minDistance) {
        minDistance = distance;
        closestMatch = token;
      }
    }

    // Consider it a match if distance is small enough
    if (minDistance < 50) {
      return {
        type: 'close',
        token: closestMatch,
        confidence: Math.max(0, 1 - (minDistance / 255)),
        distance: minDistance
      };
    }

    return null;
  }

  /**
   * Generate replacement suggestion
   */
  generateReplacement(rgbaPattern, colorMatch) {
    const { r, g, b, a } = rgbaPattern;
    
    if (!colorMatch) {
      return {
        type: 'no_match',
        original: rgbaPattern.fullMatch,
        suggestion: null,
        reason: 'No matching color token found'
      };
    }

    const { token, type, confidence } = colorMatch;
    
    // Common alpha values that might have semantic meaning
    const commonAlphas = {
      0.05: 'subtle',
      0.1: 'light',
      0.15: 'soft',
      0.2: 'medium',
      0.3: 'emphasis',
      0.4: 'strong',
      0.5: 'semi',
      0.6: 'bold',
      0.7: 'heavy',
      0.8: 'intense',
      0.9: 'almost-opaque'
    };

    let replacement;
    let reasoning = '';

    if (a === 1.0) {
      // Fully opaque - use the color token directly
      replacement = `var(--${token.variable})`;
      reasoning = 'Fully opaque color matches existing token';
    } else if (token.hasRgbVar) {
      // Use existing RGB variable
      replacement = `rgba(var(--${token.variable}-rgb), ${a})`;
      reasoning = 'Using existing RGB variable for transparency';
    } else {
      // Suggest creating an RGB variable or using rgba with the token
      const alphaName = commonAlphas[a] || a.toString().replace('.', '-');
      const newVarName = `${token.variable}-${alphaName}`;
      
      replacement = `rgba(${r}, ${g}, ${b}, ${a})`;
      reasoning = `Consider creating --${newVarName}: rgba(var(--${token.variable}-rgb), ${a})`;
    }

    return {
      type: 'replacement',
      original: rgbaPattern.fullMatch,
      suggestion: replacement,
      confidence,
      tokenUsed: token.variable,
      reasoning,
      needsRgbVar: !token.hasRgbVar && a < 1.0
    };
  }

  /**
   * Scan a single CSS file
   */
  scanFile(filePath) {
    if (this.verbose) {
      console.log(`🔍 Scanning: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf8');
    const rgbaPatterns = this.extractRgbaPatterns(content);
    const fileReplacements = [];

    this.report.filesScanned++;
    this.report.rgbaFound += rgbaPatterns.length;

    for (const pattern of rgbaPatterns) {
      const { r, g, b, a } = pattern;
      const colorMatch = this.findColorMatch(r, g, b);
      const replacement = this.generateReplacement(pattern, colorMatch);

      if (replacement.type === 'replacement') {
        this.report.potentialReplacements++;
        fileReplacements.push({
          file: filePath,
          pattern,
          replacement,
          line: this.getLineNumber(content, pattern.index)
        });
      }

      // Track unique rgba patterns
      this.rgbaPatterns.add(`rgba(${r}, ${g}, ${b}, ${a})`);
    }

    if (fileReplacements.length > 0) {
      this.replacements.push(...fileReplacements);
    }

    return fileReplacements;
  }

  /**
   * Get line number for a given index in content
   */
  getLineNumber(content, index) {
    return content.substring(0, index).split('\n').length;
  }

  /**
   * Create backup of files before modification
   */
  createBackup() {
    if (!fs.existsSync(this.backupDir)) {
      fs.mkdirSync(this.backupDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = path.join(this.backupDir, `backup-${timestamp}`);
    
    console.log(`💾 Creating backup at: ${backupPath}`);
    
    try {
      execSync(`cp -r ${this.cssDir} ${backupPath}`);
      console.log('✅ Backup created successfully');
      return backupPath;
    } catch (error) {
      console.error('❌ Failed to create backup:', error.message);
      throw error;
    }
  }

  /**
   * Apply replacements to files
   */
  applyReplacements(replacements = null) {
    const toApply = replacements || this.replacements;
    
    if (toApply.length === 0) {
      console.log('ℹ️  No replacements to apply');
      return;
    }

    console.log(`🔄 Applying ${toApply.length} replacements...`);

    // Group by file
    const fileGroups = {};
    for (const replacement of toApply) {
      if (!fileGroups[replacement.file]) {
        fileGroups[replacement.file] = [];
      }
      fileGroups[replacement.file].push(replacement);
    }

    for (const [filePath, fileReplacements] of Object.entries(fileGroups)) {
      try {
        let content = fs.readFileSync(filePath, 'utf8');
        
        // Sort by index in reverse order to avoid position shifts
        fileReplacements.sort((a, b) => b.pattern.index - a.pattern.index);
        
        for (const replacement of fileReplacements) {
          const { pattern, replacement: repl } = replacement;
          const before = content.substring(0, pattern.index);
          const after = content.substring(pattern.index + pattern.fullMatch.length);
          content = before + repl.suggestion + after;
          
          this.report.replacementsMade++;
          
          if (this.verbose) {
            console.log(`  ${path.relative(process.cwd(), filePath)}:${replacement.line}`);
            console.log(`    ${pattern.fullMatch} → ${repl.suggestion}`);
          }
        }

        if (!this.dryRun) {
          fs.writeFileSync(filePath, content, 'utf8');
        }

      } catch (error) {
        const errorMsg = `Failed to process ${filePath}: ${error.message}`;
        console.error(`❌ ${errorMsg}`);
        this.report.errors.push(errorMsg);
      }
    }

    if (this.dryRun) {
      console.log('🧪 Dry run completed - no files were modified');
    } else {
      console.log(`✅ Applied ${this.report.replacementsMade} replacements`);
    }
  }

  /**
   * Generate a detailed report
   */
  generateReport() {
    console.log('\n📊 RGBA Scan Report');
    console.log('='.repeat(50));
    console.log(`Files scanned: ${this.report.filesScanned}`);
    console.log(`RGBA patterns found: ${this.report.rgbaFound}`);
    console.log(`Potential replacements: ${this.report.potentialReplacements}`);
    console.log(`Replacements made: ${this.report.replacementsMade}`);
    console.log(`Unique RGBA patterns: ${this.rgbaPatterns.size}`);

    if (this.report.errors.length > 0) {
      console.log(`\n❌ Errors (${this.report.errors.length}):`);
      for (const error of this.report.errors) {
        console.log(`  ${error}`);
      }
    }

    // Show unique patterns
    if (this.rgbaPatterns.size > 0) {
      console.log('\n🎨 Unique RGBA patterns found:');
      const sortedPatterns = Array.from(this.rgbaPatterns).sort();
      for (const pattern of sortedPatterns) {
        console.log(`  ${pattern}`);
      }
    }

    // Show replacement suggestions
    if (this.replacements.length > 0) {
      console.log('\n🔄 Replacement suggestions:');
      const groupedByToken = {};
      
      for (const replacement of this.replacements) {
        const tokenUsed = replacement.replacement.tokenUsed || 'no-match';
        if (!groupedByToken[tokenUsed]) {
          groupedByToken[tokenUsed] = [];
        }
        groupedByToken[tokenUsed].push(replacement);
      }

      for (const [token, replacements] of Object.entries(groupedByToken)) {
        console.log(`\n  --${token}:`);
        for (const repl of replacements) {
          const relativePath = path.relative(process.cwd(), repl.file);
          console.log(`    ${relativePath}:${repl.line}`);
          console.log(`      ${repl.pattern.fullMatch} → ${repl.replacement.suggestion}`);
          if (repl.replacement.reasoning) {
            console.log(`      💡 ${repl.replacement.reasoning}`);
          }
        }
      }
    }

    // Suggestions for missing RGB variables
    const missingRgbVars = new Set();
    for (const replacement of this.replacements) {
      if (replacement.replacement.needsRgbVar) {
        missingRgbVars.add(replacement.replacement.tokenUsed);
      }
    }

    if (missingRgbVars.size > 0) {
      console.log('\n💡 Suggested RGB variables to add to colors.css:');
      for (const tokenName of missingRgbVars) {
        const token = Array.from(this.colorTokens.values()).find(t => t.variable === tokenName);
        if (token && token.rgb) {
          console.log(`  --${tokenName}-rgb: ${token.rgb.r}, ${token.rgb.g}, ${token.rgb.b};`);
        }
      }
    }
  }

  /**
   * Save detailed report to file
   */
  saveReport(filename = 'rgba-scan-report.json') {
    const reportData = {
      timestamp: new Date().toISOString(),
      summary: this.report,
      colorTokens: Array.from(this.colorTokens.entries()),
      rgbaPatterns: Array.from(this.rgbaPatterns),
      replacements: this.replacements.map(r => ({
        file: path.relative(process.cwd(), r.file),
        line: r.line,
        original: r.pattern.fullMatch,
        suggestion: r.replacement.suggestion,
        confidence: r.replacement.confidence,
        reasoning: r.replacement.reasoning
      }))
    };

    fs.writeFileSync(filename, JSON.stringify(reportData, null, 2));
    console.log(`\n📄 Detailed report saved to: ${filename}`);
  }

  /**
   * Main scan function
   */
  async scan() {
    console.log('🚀 Starting RGBA scan...');
    
    try {
      // Parse color tokens
      this.parseColorTokens();
      
      // Get CSS files
      const cssFiles = this.getCSSFiles();
      console.log(`📁 Found ${cssFiles.length} CSS files to scan`);
      
      // Scan each file
      for (const file of cssFiles) {
        this.scanFile(file);
      }
      
      // Generate and show report
      this.generateReport();
      
      return this.replacements;
      
    } catch (error) {
      console.error('❌ Scan failed:', error.message);
      throw error;
    }
  }

  /**
   * Interactive replacement process
   */
  async interactiveReplace() {
    if (this.replacements.length === 0) {
      console.log('ℹ️  No replacements available');
      return;
    }

    console.log('\n🔧 Interactive replacement mode');
    console.log('Review each replacement (y/n/a for yes/no/all):');

    const selectedReplacements = [];
    
    for (let i = 0; i < this.replacements.length; i++) {
      const replacement = this.replacements[i];
      const relativePath = path.relative(process.cwd(), replacement.file);
      
      console.log(`\n[${i + 1}/${this.replacements.length}] ${relativePath}:${replacement.line}`);
      console.log(`  ${replacement.pattern.fullMatch}`);
      console.log(`  → ${replacement.replacement.suggestion}`);
      console.log(`  💡 ${replacement.replacement.reasoning}`);
      console.log(`  🎯 Confidence: ${(replacement.replacement.confidence * 100).toFixed(1)}%`);
      
      // In a real interactive scenario, you'd use readline here
      // For this implementation, we'll assume 'y' for high confidence replacements
      if (replacement.replacement.confidence > 0.8) {
        selectedReplacements.push(replacement);
        console.log('  ✅ Auto-selected (high confidence)');
      } else {
        console.log('  ⏭️  Skipped (low confidence)');
      }
    }

    return selectedReplacements;
  }
}

/**
 * CLI Interface
 */
function main() {
  const args = process.argv.slice(2);
  const options = {
    dryRun: args.includes('--dry-run'),
    verbose: args.includes('--verbose') || args.includes('-v'),
    interactive: args.includes('--interactive'),
    autoReplace: args.includes('--auto-replace'),
    backupDir: 'rgba-backup'
  };

  console.log('🎨 RGBA Values Scanner and Replacer');
  console.log('===================================\n');

  if (args.includes('--help') || args.includes('-h')) {
    console.log('Usage: node scan-rgba-values.js [options]');
    console.log('\nOptions:');
    console.log('  --dry-run       Scan only, don\'t modify files');
    console.log('  --verbose, -v   Show detailed output');
    console.log('  --interactive   Review each replacement');
    console.log('  --auto-replace  Auto-replace high confidence matches');
    console.log('  --help, -h      Show this help');
    console.log('\nExamples:');
    console.log('  node scan-rgba-values.js --dry-run --verbose');
    console.log('  node scan-rgba-values.js --interactive');
    console.log('  node scan-rgba-values.js --auto-replace');
    return;
  }

  const scanner = new RGBAScanner(options);

  scanner.scan()
    .then(async (replacements) => {
      if (replacements.length === 0) {
        console.log('\n🎉 No RGBA patterns need replacement!');
        return;
      }

      // Save report
      scanner.saveReport();

      if (options.dryRun) {
        console.log('\n🧪 Dry run completed - use --auto-replace or --interactive to apply changes');
        return;
      }

      let selectedReplacements = replacements;

      if (options.interactive) {
        selectedReplacements = await scanner.interactiveReplace();
      } else if (options.autoReplace) {
        // Auto-select high confidence replacements
        selectedReplacements = replacements.filter(r => r.replacement.confidence > 0.8);
        console.log(`\n🤖 Auto-selected ${selectedReplacements.length} high-confidence replacements`);
      } else {
        console.log('\n⚠️  Use --interactive or --auto-replace to apply changes');
        return;
      }

      if (selectedReplacements.length > 0) {
        // Create backup
        const backupPath = scanner.createBackup();
        console.log(`💡 To rollback: cp -r ${backupPath}/* ${scanner.cssDir}/`);

        // Apply replacements
        scanner.applyReplacements(selectedReplacements);
        
        console.log('\n🎉 Replacement completed!');
      }
    })
    .catch(error => {
      console.error('💥 Error:', error.message);
      process.exit(1);
    });
}

// Export for testing
module.exports = RGBAScanner;

// Run if called directly
if (require.main === module) {
  main();
}