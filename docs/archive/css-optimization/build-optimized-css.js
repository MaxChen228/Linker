#!/usr/bin/env node

/**
 * CSS Tree-shaking Build Script
 * 
 * This script builds optimized CSS by:
 * 1. Processing all CSS files through PostCSS with PurgeCSS
 * 2. Generating size comparison reports
 * 3. Creating production-ready optimized builds
 */

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');
const glob = require('glob');

// Set production environment
process.env.NODE_ENV = 'production';

// Import PostCSS configuration
const postcssConfig = require('./postcss.config.js');

// Output directories
const DIST_DIR = './web/static/css/dist';
const REPORTS_DIR = './reports/css-tree-shaking';

// Ensure output directories exist
function ensureDirectories() {
  [DIST_DIR, REPORTS_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

// Get file size in bytes
function getFileSize(filePath) {
  try {
    return fs.statSync(filePath).size;
  } catch (error) {
    return 0;
  }
}

// Format bytes to human readable format
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Calculate percentage reduction
function calculateReduction(originalSize, optimizedSize) {
  if (originalSize === 0) return 0;
  return ((originalSize - optimizedSize) / originalSize * 100).toFixed(2);
}

// Process a single CSS file
async function processCSSFile(inputFile, outputFile) {
  try {
    console.log(`Processing: ${inputFile}`);
    
    // Read original CSS
    const css = fs.readFileSync(inputFile, 'utf8');
    const originalSize = Buffer.byteLength(css, 'utf8');
    
    // Process with PostCSS (includes PurgeCSS and cssnano)
    const result = await postcss(postcssConfig.plugins).process(css, {
      from: inputFile,
      to: outputFile
    });
    
    // Write optimized CSS
    fs.writeFileSync(outputFile, result.css);
    
    const optimizedSize = getFileSize(outputFile);
    const reduction = calculateReduction(originalSize, optimizedSize);
    
    return {
      file: path.basename(inputFile),
      originalSize,
      optimizedSize,
      reduction: parseFloat(reduction),
      savings: originalSize - optimizedSize
    };
  } catch (error) {
    console.error(`Error processing ${inputFile}:`, error.message);
    return null;
  }
}

// Main build function
async function buildOptimizedCSS() {
  console.log('🚀 Starting CSS tree-shaking build...\n');
  
  ensureDirectories();
  
  // Find all CSS files to process
  const cssFiles = glob.sync('web/static/css/**/*.css', {
    ignore: [
      'web/static/css/dist/**',
      'web/static/css/**/*.min.css'
    ]
  });
  
  console.log(`Found ${cssFiles.length} CSS files to process\n`);
  
  const results = [];
  let totalOriginalSize = 0;
  let totalOptimizedSize = 0;
  
  // Process each CSS file
  for (const inputFile of cssFiles) {
    // Create output path maintaining directory structure
    const relativePath = path.relative('web/static/css', inputFile);
    const outputFile = path.join(DIST_DIR, relativePath);
    
    // Ensure output directory exists
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const result = await processCSSFile(inputFile, outputFile);
    
    if (result) {
      results.push(result);
      totalOriginalSize += result.originalSize;
      totalOptimizedSize += result.optimizedSize;
      
      console.log(`✅ ${result.file}: ${formatBytes(result.originalSize)} → ${formatBytes(result.optimizedSize)} (${result.reduction}% reduction)`);
    }
  }
  
  const totalReduction = calculateReduction(totalOriginalSize, totalOptimizedSize);
  const totalSavings = totalOriginalSize - totalOptimizedSize;
  
  console.log('\n📊 Summary:');
  console.log(`Total original size: ${formatBytes(totalOriginalSize)}`);
  console.log(`Total optimized size: ${formatBytes(totalOptimizedSize)}`);
  console.log(`Total savings: ${formatBytes(totalSavings)} (${totalReduction}% reduction)`);
  
  // Generate detailed report
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalFiles: results.length,
      originalSize: totalOriginalSize,
      optimizedSize: totalOptimizedSize,
      totalSavings,
      totalReduction: parseFloat(totalReduction)
    },
    files: results.sort((a, b) => b.savings - a.savings) // Sort by savings (highest first)
  };
  
  // Write JSON report
  const reportFile = path.join(REPORTS_DIR, 'tree-shaking-report.json');
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  
  // Generate markdown report
  const markdownReport = generateMarkdownReport(report);
  const markdownFile = path.join(REPORTS_DIR, 'tree-shaking-report.md');
  fs.writeFileSync(markdownFile, markdownReport);
  
  console.log(`\n📁 Reports generated:`);
  console.log(`  JSON: ${reportFile}`);
  console.log(`  Markdown: ${markdownFile}`);
  
  // Create a summary for easy integration
  createBuildSummary(report);
  
  console.log('\n✨ CSS tree-shaking build completed successfully!');
}

// Generate markdown report
function generateMarkdownReport(report) {
  const { summary, files } = report;
  
  let markdown = `# CSS Tree-shaking Report

Generated: ${new Date(report.timestamp).toLocaleString()}

## Summary

- **Total Files Processed**: ${summary.totalFiles}
- **Original Total Size**: ${formatBytes(summary.originalSize)}
- **Optimized Total Size**: ${formatBytes(summary.optimizedSize)}
- **Total Savings**: ${formatBytes(summary.totalSavings)} (${summary.totalReduction}% reduction)

## File Details

| File | Original Size | Optimized Size | Savings | Reduction % |
|------|---------------|----------------|---------|-------------|
`;

  files.forEach(file => {
    markdown += `| ${file.file} | ${formatBytes(file.originalSize)} | ${formatBytes(file.optimizedSize)} | ${formatBytes(file.savings)} | ${file.reduction}% |\n`;
  });
  
  markdown += `
## Top 5 Space Savers

`;

  files.slice(0, 5).forEach((file, index) => {
    markdown += `${index + 1}. **${file.file}**: ${formatBytes(file.savings)} saved (${file.reduction}% reduction)\n`;
  });
  
  markdown += `
## Build Configuration

This build used the following optimizations:

- **PurgeCSS**: Removed unused CSS rules based on HTML templates and JavaScript files
- **PostCSS Plugins**:
  - \`postcss-combine-duplicated-selectors\`: Combined duplicate selectors
  - \`postcss-merge-rules\`: Merged similar CSS rules
  - \`postcss-discard-duplicates\`: Removed duplicate rules
  - \`cssnano\`: Minified and optimized CSS

## Safelist Configuration

The build preserved:
- Essential HTML elements and common component classes
- Design system utility classes and tokens
- Dynamic classes and data attributes
- CSS variables and keyframe animations
- Interactive states and responsive variants

## Next Steps

1. Review the optimized CSS files in \`web/static/css/dist/\`
2. Test the application to ensure no styles were incorrectly removed
3. Update your production deployment to use the optimized CSS files
4. Monitor for any missing styles and update the safelist if needed
`;

  return markdown;
}

// Create a simple build summary file
function createBuildSummary(report) {
  const summary = {
    success: true,
    timestamp: report.timestamp,
    totalSavings: formatBytes(report.summary.totalSavings),
    reductionPercentage: report.summary.totalReduction,
    filesProcessed: report.summary.totalFiles,
    outputDir: DIST_DIR
  };
  
  fs.writeFileSync(
    path.join(REPORTS_DIR, 'build-summary.json'),
    JSON.stringify(summary, null, 2)
  );
}

// Error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run the build
if (require.main === module) {
  buildOptimizedCSS().catch(error => {
    console.error('❌ Build failed:', error);
    process.exit(1);
  });
}

module.exports = { buildOptimizedCSS };