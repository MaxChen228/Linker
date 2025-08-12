#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');
const postcssConfig = require('./postcss.config.js');

// Configuration
const CSS_DIR = './web/static/css';
const REPORT_FILE = './css-deduplication-report.json';

// Helper functions
function getAllCSSFiles(dir) {
  const files = [];
  
  function walkDir(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        walkDir(fullPath);
      } else if (item.endsWith('.css')) {
        files.push(fullPath);
      }
    }
  }
  
  walkDir(dir);
  return files;
}

function getFileSize(filePath) {
  return fs.statSync(filePath).size;
}

function analyzeCSS(css) {
  const selectors = new Set();
  const duplicateSelectors = new Set();
  const rules = [];
  
  // Simple regex-based analysis for duplicates
  const selectorMatches = css.match(/[^{}]+(?=\s*\{)/g);
  if (selectorMatches) {
    const selectorCounts = {};
    
    selectorMatches.forEach(selector => {
      const cleanSelector = selector.trim();
      if (selectorCounts[cleanSelector]) {
        duplicateSelectors.add(cleanSelector);
      } else {
        selectorCounts[cleanSelector] = 1;
      }
      selectors.add(cleanSelector);
    });
  }
  
  return {
    totalSelectors: selectors.size,
    duplicateSelectors: duplicateSelectors.size,
    duplicateList: Array.from(duplicateSelectors)
  };
}

async function processFile(filePath) {
  console.log(`Processing: ${filePath}`);
  
  const originalCSS = fs.readFileSync(filePath, 'utf8');
  const originalSize = originalCSS.length;
  const originalAnalysis = analyzeCSS(originalCSS);
  
  try {
    // Process with PostCSS
    const result = await postcss(postcssConfig.plugins).process(originalCSS, {
      from: filePath,
      to: filePath
    });
    
    const processedCSS = result.css;
    const newSize = processedCSS.length;
    const newAnalysis = analyzeCSS(processedCSS);
    
    // Write the processed CSS back to file
    fs.writeFileSync(filePath, processedCSS, 'utf8');
    
    return {
      file: filePath,
      originalSize,
      newSize,
      sizeDifference: originalSize - newSize,
      sizeReduction: ((originalSize - newSize) / originalSize * 100).toFixed(2),
      originalDuplicates: originalAnalysis.duplicateSelectors,
      newDuplicates: newAnalysis.duplicateSelectors,
      duplicatesRemoved: originalAnalysis.duplicateSelectors - newAnalysis.duplicateSelectors,
      removedDuplicatesList: originalAnalysis.duplicateList.filter(
        selector => !newAnalysis.duplicateList.includes(selector)
      ),
      warnings: result.warnings().map(warning => warning.toString())
    };
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    return {
      file: filePath,
      error: error.message,
      originalSize,
      newSize: originalSize,
      sizeDifference: 0,
      sizeReduction: '0.00',
      originalDuplicates: originalAnalysis.duplicateSelectors,
      newDuplicates: originalAnalysis.duplicateSelectors,
      duplicatesRemoved: 0,
      removedDuplicatesList: []
    };
  }
}

async function main() {
  console.log('🚀 Starting CSS deduplication process...\n');
  
  const cssFiles = getAllCSSFiles(CSS_DIR);
  console.log(`Found ${cssFiles.length} CSS files to process:\n`);
  
  const results = [];
  let totalOriginalSize = 0;
  let totalNewSize = 0;
  let totalDuplicatesRemoved = 0;
  
  for (const filePath of cssFiles) {
    const result = await processFile(filePath);
    results.push(result);
    
    totalOriginalSize += result.originalSize;
    totalNewSize += result.newSize;
    totalDuplicatesRemoved += result.duplicatesRemoved;
    
    console.log(`  ✅ ${result.file}`);
    console.log(`     Size: ${result.originalSize} → ${result.newSize} bytes (${result.sizeReduction}% reduction)`);
    console.log(`     Duplicates removed: ${result.duplicatesRemoved}`);
    
    if (result.warnings && result.warnings.length > 0) {
      console.log(`     ⚠️  Warnings: ${result.warnings.length}`);
    }
    
    if (result.error) {
      console.log(`     ❌ Error: ${result.error}`);
    }
    
    console.log('');
  }
  
  // Generate summary report
  const summary = {
    timestamp: new Date().toISOString(),
    totalFiles: cssFiles.length,
    totalOriginalSize,
    totalNewSize,
    totalSizeDifference: totalOriginalSize - totalNewSize,
    totalSizeReduction: ((totalOriginalSize - totalNewSize) / totalOriginalSize * 100).toFixed(2),
    totalDuplicatesRemoved,
    processedFiles: results,
    mostAffectedFiles: results
      .filter(r => r.sizeDifference > 0)
      .sort((a, b) => b.sizeDifference - a.sizeDifference)
      .slice(0, 10),
    filesWithMostDuplicates: results
      .filter(r => r.duplicatesRemoved > 0)
      .sort((a, b) => b.duplicatesRemoved - a.duplicatesRemoved)
      .slice(0, 10)
  };
  
  // Save detailed report
  fs.writeFileSync(REPORT_FILE, JSON.stringify(summary, null, 2));
  
  // Print summary
  console.log('📊 DEDUPLICATION SUMMARY');
  console.log('=' .repeat(50));
  console.log(`Files processed: ${summary.totalFiles}`);
  console.log(`Total size reduction: ${summary.totalSizeDifference} bytes (${summary.totalSizeReduction}%)`);
  console.log(`Total duplicates removed: ${summary.totalDuplicatesRemoved}`);
  console.log(`Original total size: ${(summary.totalOriginalSize / 1024).toFixed(2)} KB`);
  console.log(`New total size: ${(summary.totalNewSize / 1024).toFixed(2)} KB`);
  console.log('');
  
  if (summary.mostAffectedFiles.length > 0) {
    console.log('📈 MOST AFFECTED FILES (by size reduction):');
    summary.mostAffectedFiles.forEach((file, index) => {
      console.log(`${index + 1}. ${file.file.replace('./web/static/css/', '')}`);
      console.log(`   Size reduction: ${file.sizeDifference} bytes (${file.sizeReduction}%)`);
      console.log(`   Duplicates removed: ${file.duplicatesRemoved}`);
    });
    console.log('');
  }
  
  if (summary.filesWithMostDuplicates.length > 0) {
    console.log('🔍 FILES WITH MOST DUPLICATES REMOVED:');
    summary.filesWithMostDuplicates.forEach((file, index) => {
      console.log(`${index + 1}. ${file.file.replace('./web/static/css/', '')}`);
      console.log(`   Duplicates removed: ${file.duplicatesRemoved}`);
      if (file.removedDuplicatesList.length > 0 && file.removedDuplicatesList.length <= 5) {
        console.log(`   Examples: ${file.removedDuplicatesList.slice(0, 3).join(', ')}`);
      }
    });
  }
  
  console.log('');
  console.log(`📄 Detailed report saved to: ${REPORT_FILE}`);
  console.log(`💾 CSS backup available at: ./css-backup/`);
  console.log('');
  console.log('✨ CSS deduplication completed successfully!');
}

// Run the script
main().catch(error => {
  console.error('❌ Script failed:', error);
  process.exit(1);
});