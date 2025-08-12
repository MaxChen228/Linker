#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');

// Simple PostCSS config for quick processing
const quickPlugins = [
  require('postcss-combine-duplicated-selectors')({
    removeDuplicatedProperties: true,
    removeDuplicatedValues: true
  })
];

const CSS_DIR = './web/static/css';

function getAllCSSFiles(dir) {
  const files = [];
  
  function walkDir(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !fullPath.includes('dist')) { // Skip dist folder for speed
        walkDir(fullPath);
      } else if (item.endsWith('.css') && !fullPath.includes('.min.css')) {
        files.push(fullPath);
      }
    }
  }
  
  walkDir(dir);
  return files;
}

async function processFile(filePath) {
  const originalCSS = fs.readFileSync(filePath, 'utf8');
  const originalSize = originalCSS.length;
  
  try {
    const result = await postcss(quickPlugins).process(originalCSS, {
      from: filePath,
      to: filePath
    });
    
    const processedCSS = result.css;
    const newSize = processedCSS.length;
    
    // Only write if there's an actual change
    if (originalSize !== newSize) {
      fs.writeFileSync(filePath, processedCSS, 'utf8');
    }
    
    return {
      file: filePath.replace('./web/static/css/', ''),
      originalSize,
      newSize,
      sizeDifference: originalSize - newSize,
      sizeReduction: ((originalSize - newSize) / originalSize * 100).toFixed(2)
    };
  } catch (error) {
    return {
      file: filePath.replace('./web/static/css/', ''),
      error: error.message,
      originalSize,
      newSize: originalSize,
      sizeDifference: 0,
      sizeReduction: '0.00'
    };
  }
}

async function main() {
  console.log('🚀 Quick CSS deduplication starting...\n');
  
  const cssFiles = getAllCSSFiles(CSS_DIR);
  console.log(`Processing ${cssFiles.length} CSS files (excluding dist and min files)...\n`);
  
  const results = [];
  let totalOriginalSize = 0;
  let totalNewSize = 0;
  let filesWithReduction = 0;
  
  for (const filePath of cssFiles) {
    const result = await processFile(filePath);
    results.push(result);
    
    totalOriginalSize += result.originalSize;
    totalNewSize += result.newSize;
    
    if (result.sizeDifference > 0) {
      filesWithReduction++;
      console.log(`✅ ${result.file} - ${result.sizeDifference} bytes saved (${result.sizeReduction}%)`);
    } else {
      console.log(`📄 ${result.file} - no duplicates found`);
    }
  }
  
  // Generate summary report
  const summary = {
    timestamp: new Date().toISOString(),
    totalFiles: cssFiles.length,
    filesWithReduction,
    totalOriginalSize,
    totalNewSize,
    totalSizeDifference: totalOriginalSize - totalNewSize,
    totalSizeReduction: ((totalOriginalSize - totalNewSize) / totalOriginalSize * 100).toFixed(2),
    topReductions: results
      .filter(r => r.sizeDifference > 0)
      .sort((a, b) => b.sizeDifference - a.sizeDifference)
      .slice(0, 10)
  };
  
  // Save report
  fs.writeFileSync('./css-deduplication-summary.json', JSON.stringify(summary, null, 2));
  
  // Print summary
  console.log('\n📊 DEDUPLICATION SUMMARY');
  console.log('=' .repeat(50));
  console.log(`Files processed: ${summary.totalFiles}`);
  console.log(`Files with duplicates removed: ${summary.filesWithReduction}`);
  console.log(`Total size reduction: ${summary.totalSizeDifference} bytes (${summary.totalSizeReduction}%)`);
  console.log(`Original total size: ${(summary.totalOriginalSize / 1024).toFixed(2)} KB`);
  console.log(`New total size: ${(summary.totalNewSize / 1024).toFixed(2)} KB`);
  
  if (summary.topReductions.length > 0) {
    console.log('\n📈 TOP FILES BY SIZE REDUCTION:');
    summary.topReductions.slice(0, 5).forEach((file, index) => {
      console.log(`${index + 1}. ${file.file}: ${file.sizeDifference} bytes (${file.sizeReduction}%)`);
    });
  }
  
  console.log(`\n📄 Report saved to: css-deduplication-summary.json`);
  console.log('✨ Deduplication completed!');
}

main().catch(error => {
  console.error('❌ Error:', error);
  process.exit(1);
});