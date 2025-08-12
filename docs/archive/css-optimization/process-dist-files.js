#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');

const plugins = [
  require('postcss-combine-duplicated-selectors')({
    removeDuplicatedProperties: true,
    removeDuplicatedValues: true
  })
];

async function processDistFiles() {
  const distDir = './web/static/css/dist';
  
  if (!fs.existsSync(distDir)) {
    console.log('No dist directory found');
    return;
  }
  
  const files = fs.readdirSync(distDir).filter(f => f.endsWith('.css'));
  
  console.log('Processing dist files...\n');
  
  for (const file of files) {
    const filePath = path.join(distDir, file);
    const originalCSS = fs.readFileSync(filePath, 'utf8');
    const originalSize = originalCSS.length;
    
    try {
      const result = await postcss(plugins).process(originalCSS, {
        from: filePath,
        to: filePath
      });
      
      const processedCSS = result.css;
      const newSize = processedCSS.length;
      const reduction = originalSize - newSize;
      const percentage = ((reduction / originalSize) * 100).toFixed(2);
      
      if (reduction > 0) {
        fs.writeFileSync(filePath, processedCSS, 'utf8');
        console.log(`✅ ${file}: ${reduction} bytes saved (${percentage}%)`);
        console.log(`   ${(originalSize / 1024).toFixed(2)} KB → ${(newSize / 1024).toFixed(2)} KB`);
      } else {
        console.log(`📄 ${file}: no duplicates found`);
      }
    } catch (error) {
      console.log(`❌ ${file}: Error - ${error.message}`);
    }
  }
}

processDistFiles().catch(console.error);