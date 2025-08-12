#!/usr/bin/env node

/**
 * Hardcoded PX Value Scanner and Replacer
 * 
 * This tool scans CSS files for hardcoded px values and suggests replacements
 * with CSS custom properties (spacing tokens). It excludes small border values
 * (1-4px) and provides safe, reversible batch replacement functionality.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

class PxValueScanner {
  constructor() {
    // Mapping of px values to spacing tokens based on the existing spacing.css
    this.spacingTokens = {
      '0px': 'var(--space-0)',
      '2px': 'var(--space-0-25)',
      '3px': 'var(--space-0-375)',
      '4px': 'var(--space-1)',
      '6px': 'var(--space-1-5)',
      '8px': 'var(--space-2)',
      '10px': 'var(--space-2-5)',
      '12px': 'var(--space-3)',
      '16px': 'var(--space-4)',
      '20px': 'var(--space-5)',
      '24px': 'var(--space-6)',
      '32px': 'var(--space-8)',
      '40px': 'var(--space-10)',
      '48px': 'var(--space-12)',
      '56px': 'var(--space-7)',
      '60px': 'var(--space-15)',
      '64px': 'var(--space-16)',
      '80px': 'var(--space-20)',
      '400px': 'var(--space-50)',
      '-8px': 'var(--space-n2)'
    };

    // Properties to exclude from replacement (border-related)
    this.excludedProperties = [
      'border',
      'border-width',
      'border-top-width',
      'border-right-width',
      'border-bottom-width',
      'border-left-width',
      'border-top',
      'border-right',
      'border-bottom',
      'border-left',
      'outline',
      'outline-width',
      'outline-offset'
    ];

    // Values to exclude (small border values)
    this.excludedValues = ['1px', '2px', '3px', '4px'];

    this.findings = [];
    this.replacements = [];
  }

  /**
   * Scan directory for CSS files
   */
  async scanDirectory(dirPath = './web/static/css') {
    const cssFiles = this.findCssFiles(dirPath);
    console.log(`Found ${cssFiles.length} CSS files to scan...\n`);

    for (const filePath of cssFiles) {
      await this.scanFile(filePath);
    }

    return this.findings;
  }

  /**
   * Find all CSS files in directory recursively
   */
  findCssFiles(dirPath) {
    const cssFiles = [];

    const scanDir = (currentPath) => {
      if (!fs.existsSync(currentPath)) {
        console.log(`Warning: Directory ${currentPath} does not exist`);
        return;
      }

      const items = fs.readdirSync(currentPath);
      
      for (const item of items) {
        const fullPath = path.join(currentPath, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
          // Skip node_modules and dist directories
          if (!item.includes('node_modules') && !item.includes('dist')) {
            scanDir(fullPath);
          }
        } else if (item.endsWith('.css')) {
          cssFiles.push(fullPath);
        }
      }
    };

    scanDir(dirPath);
    return cssFiles;
  }

  /**
   * Scan individual CSS file for hardcoded px values
   */
  async scanFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const lineNumber = i + 1;

        // Find all px values in the line
        const pxMatches = line.match(/(\S+)\s*:\s*[^;]*?(\d+px)/g);
        
        if (pxMatches) {
          for (const match of pxMatches) {
            this.analyzePxValue(filePath, lineNumber, line, match);
          }
        }
      }
    } catch (error) {
      console.error(`Error reading file ${filePath}:`, error.message);
    }
  }

  /**
   * Analyze individual px value and determine if it should be replaced
   */
  analyzePxValue(filePath, lineNumber, line, match) {
    // Extract property and value
    const propertyMatch = match.match(/(\S+)\s*:/);
    const valueMatch = match.match(/(\d+px)/);

    if (!propertyMatch || !valueMatch) return;

    const property = propertyMatch[1].trim();
    const pxValue = valueMatch[1];

    // Skip if property is in excluded list
    if (this.excludedProperties.some(excluded => property.includes(excluded))) {
      return;
    }

    // Skip small border values
    if (this.excludedValues.includes(pxValue)) {
      return;
    }

    // Skip if inside CSS variable definition
    if (line.includes('--') && line.includes(':')) {
      return;
    }

    const finding = {
      file: filePath,
      line: lineNumber,
      property,
      value: pxValue,
      fullLine: line.trim(),
      suggestedToken: this.spacingTokens[pxValue] || null,
      replaceable: !!this.spacingTokens[pxValue]
    };

    this.findings.push(finding);
  }

  /**
   * Generate detailed report
   */
  generateReport() {
    const replaceableFindings = this.findings.filter(f => f.replaceable);
    const unreplaceableFindings = this.findings.filter(f => !f.replaceable);

    console.log('='.repeat(80));
    console.log('HARDCODED PX VALUES SCAN REPORT');
    console.log('='.repeat(80));
    console.log();

    console.log(`📊 Summary:`);
    console.log(`   Total findings: ${this.findings.length}`);
    console.log(`   Replaceable with tokens: ${replaceableFindings.length}`);
    console.log(`   Needs custom tokens: ${unreplaceableFindings.length}`);
    console.log();

    if (replaceableFindings.length > 0) {
      console.log('✅ REPLACEABLE WITH EXISTING TOKENS:');
      console.log('-'.repeat(50));
      
      const grouped = this.groupByValue(replaceableFindings);
      for (const [value, findings] of Object.entries(grouped)) {
        const token = findings[0].suggestedToken;
        console.log(`\n${value} → ${token} (${findings.length} occurrences)`);
        
        findings.forEach(finding => {
          console.log(`   📁 ${finding.file}:${finding.line}`);
          console.log(`      ${finding.property}: ${finding.value}`);
        });
      }
    }

    if (unreplaceableFindings.length > 0) {
      console.log('\n⚠️  NEEDS CUSTOM TOKENS:');
      console.log('-'.repeat(50));
      
      const grouped = this.groupByValue(unreplaceableFindings);
      for (const [value, findings] of Object.entries(grouped)) {
        console.log(`\n${value} (${findings.length} occurrences)`);
        console.log(`   Suggested token: --space-${value.replace('px', '')}`);
        
        findings.forEach(finding => {
          console.log(`   📁 ${finding.file}:${finding.line}`);
          console.log(`      ${finding.property}: ${finding.value}`);
        });
      }
    }

    console.log('\n' + '='.repeat(80));
  }

  /**
   * Group findings by px value
   */
  groupByValue(findings) {
    return findings.reduce((acc, finding) => {
      if (!acc[finding.value]) {
        acc[finding.value] = [];
      }
      acc[finding.value].push(finding);
      return acc;
    }, {});
  }

  /**
   * Create backup of files
   */
  async createBackup(files) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupDir = path.join(process.cwd(), `css-backup-${timestamp}`);
    
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
    }

    console.log(`📦 Creating backup in: ${backupDir}`);

    for (const filePath of files) {
      try {
        const relativePath = path.relative(process.cwd(), filePath);
        const backupPath = path.join(backupDir, relativePath);
        const backupDirPath = path.dirname(backupPath);

        if (!fs.existsSync(backupDirPath)) {
          fs.mkdirSync(backupDirPath, { recursive: true });
        }

        fs.copyFileSync(filePath, backupPath);
      } catch (error) {
        console.error(`Error backing up ${filePath}:`, error.message);
      }
    }

    console.log(`✅ Backup created successfully!`);
    return backupDir;
  }

  /**
   * Perform batch replacement
   */
  async performReplacements() {
    const replaceableFindings = this.findings.filter(f => f.replaceable);
    
    if (replaceableFindings.length === 0) {
      console.log('No replaceable findings to process.');
      return;
    }

    // Group by file
    const fileGroups = replaceableFindings.reduce((acc, finding) => {
      if (!acc[finding.file]) {
        acc[finding.file] = [];
      }
      acc[finding.file].push(finding);
      return acc;
    }, {});

    // Create backup
    const files = Object.keys(fileGroups);
    const backupDir = await this.createBackup(files);

    console.log(`\n🔄 Processing ${files.length} files...`);

    let totalReplacements = 0;

    for (const [filePath, findings] of Object.entries(fileGroups)) {
      try {
        let content = fs.readFileSync(filePath, 'utf8');
        let fileReplacements = 0;

        // Sort findings by line number (descending) to avoid line number shifts
        findings.sort((a, b) => b.line - a.line);

        for (const finding of findings) {
          // Create a more specific replacement pattern
          const regex = new RegExp(
            `(${finding.property}\\s*:\\s*[^;]*?)${finding.value}\\b`,
            'g'
          );
          
          const newContent = content.replace(regex, `$1${finding.suggestedToken}`);
          
          if (newContent !== content) {
            content = newContent;
            fileReplacements++;
            totalReplacements++;
          }
        }

        if (fileReplacements > 0) {
          fs.writeFileSync(filePath, content, 'utf8');
          console.log(`   ✅ ${path.relative(process.cwd(), filePath)} - ${fileReplacements} replacements`);
        }

      } catch (error) {
        console.error(`Error processing ${filePath}:`, error.message);
      }
    }

    console.log(`\n🎉 Replacement complete!`);
    console.log(`   Total replacements: ${totalReplacements}`);
    console.log(`   Backup location: ${backupDir}`);
    console.log(`\n💡 To restore from backup:`);
    console.log(`   cp -r "${backupDir}"/* ./`);
  }

  /**
   * Interactive CLI
   */
  async runInteractive() {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    const question = (prompt) => new Promise(resolve => rl.question(prompt, resolve));

    try {
      console.log('🔍 Hardcoded PX Value Scanner');
      console.log('=====================================\n');

      const scanPath = await question('Enter CSS directory path (default: ./web/static/css): ');
      const targetPath = scanPath.trim() || './web/static/css';

      console.log('\n🔍 Scanning for hardcoded px values...\n');
      await this.scanDirectory(targetPath);

      this.generateReport();

      const replaceableCount = this.findings.filter(f => f.replaceable).length;
      
      if (replaceableCount > 0) {
        const shouldReplace = await question(`\n❓ Replace ${replaceableCount} values? (y/N): `);
        
        if (shouldReplace.toLowerCase() === 'y' || shouldReplace.toLowerCase() === 'yes') {
          await this.performReplacements();
        } else {
          console.log('📋 No changes made. Report saved for reference.');
        }
      }

    } catch (error) {
      console.error('Error:', error.message);
    } finally {
      rl.close();
    }
  }
}

// CLI Usage
if (require.main === module) {
  const args = process.argv.slice(2);
  const scanner = new PxValueScanner();

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Usage: node scan-px-values.js [options]

Options:
  --scan [path]     Scan directory and generate report only
  --replace [path]  Scan and perform replacements (with backup)
  --interactive     Run in interactive mode (default)
  --help, -h        Show this help message

Examples:
  node scan-px-values.js --scan ./web/static/css
  node scan-px-values.js --replace ./web/static/css
  node scan-px-values.js --interactive
    `);
  } else if (args.includes('--scan')) {
    const pathIndex = args.indexOf('--scan') + 1;
    const scanPath = args[pathIndex] || './web/static/css';
    
    scanner.scanDirectory(scanPath).then(() => {
      scanner.generateReport();
    });
  } else if (args.includes('--replace')) {
    const pathIndex = args.indexOf('--replace') + 1;
    const scanPath = args[pathIndex] || './web/static/css';
    
    scanner.scanDirectory(scanPath).then(() => {
      scanner.generateReport();
      return scanner.performReplacements();
    });
  } else {
    // Default: interactive mode
    scanner.runInteractive();
  }
}

module.exports = PxValueScanner;