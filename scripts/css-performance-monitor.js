#!/usr/bin/env node

/**
 * CSS Performance Monitoring Tool
 * Analyzes CSS files for performance metrics, file sizes, and optimization opportunities
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class CSSPerformanceMonitor {
  constructor(cssDir = 'web/static/css') {
    this.cssDir = cssDir;
    this.results = {
      timestamp: new Date().toISOString(),
      totalFiles: 0,
      totalSize: 0,
      files: [],
      metrics: {},
      suggestions: []
    };
  }

  async analyze() {
    console.log('🔍 Starting CSS performance analysis...');
    
    await this.discoverFiles();
    await this.analyzeFiles();
    await this.generateMetrics();
    await this.generateSuggestions();
    await this.saveReport();
    
    this.displayResults();
  }

  async discoverFiles() {
    const files = await this.walkDirectory(this.cssDir);
    this.results.totalFiles = files.length;
    
    for (const file of files) {
      const stats = await fs.stat(file);
      const relativePath = path.relative(process.cwd(), file);
      
      this.results.files.push({
        path: relativePath,
        size: stats.size,
        sizeKB: Math.round(stats.size / 1024 * 100) / 100,
        modified: stats.mtime
      });
      
      this.results.totalSize += stats.size;
    }
    
    // Sort by size (largest first)
    this.results.files.sort((a, b) => b.size - a.size);
  }

  async analyzeFiles() {
    console.log('📊 Analyzing CSS content...');
    
    for (const file of this.results.files) {
      try {
        const content = await fs.readFile(file.path, 'utf8');
        const analysis = await this.analyzeFileContent(content, file.path);
        file.analysis = analysis;
      } catch (error) {
        console.warn(`⚠️  Could not analyze ${file.path}: ${error.message}`);
        file.analysis = { error: error.message };
      }
    }
  }

  async analyzeFileContent(content, filePath) {
    const lines = content.split('\n');
    const analysis = {
      lines: lines.length,
      selectors: 0,
      declarations: 0,
      comments: 0,
      emptyLines: 0,
      mediaQueries: 0,
      customProperties: 0,
      importRules: 0,
      complexSelectors: 0,
      duplicateSelectors: [],
      potentialIssues: []
    };

    // Count empty lines and comments
    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed) analysis.emptyLines++;
      if (trimmed.startsWith('/*') || trimmed.includes('/*')) analysis.comments++;
    });

    // Analyze CSS rules
    const selectorRegex = /([^{]+)\s*{/g;
    const declarationRegex = /[^{;]+:[^;}]+[;}]/g;
    const mediaQueryRegex = /@media[^{]+{/g;
    const customPropertyRegex = /--[a-zA-Z-]+:/g;
    const importRegex = /@import/g;

    // Count selectors and check for complexity
    const selectors = content.match(selectorRegex) || [];
    analysis.selectors = selectors.length;
    
    const selectorTexts = selectors.map(s => s.replace('{', '').trim());
    analysis.duplicateSelectors = this.findDuplicates(selectorTexts);
    
    // Count complex selectors (more than 3 parts)
    analysis.complexSelectors = selectorTexts.filter(s => 
      s.split(/\s+/).length > 3 || s.includes('>') || s.includes('+') || s.includes('~')
    ).length;

    // Count declarations
    analysis.declarations = (content.match(declarationRegex) || []).length;
    
    // Count media queries
    analysis.mediaQueries = (content.match(mediaQueryRegex) || []).length;
    
    // Count custom properties
    analysis.customProperties = (content.match(customPropertyRegex) || []).length;
    
    // Count import rules
    analysis.importRules = (content.match(importRegex) || []).length;

    // Identify potential issues
    if (analysis.complexSelectors > analysis.selectors * 0.3) {
      analysis.potentialIssues.push('High percentage of complex selectors');
    }
    
    if (analysis.duplicateSelectors.length > 0) {
      analysis.potentialIssues.push(`${analysis.duplicateSelectors.length} duplicate selectors found`);
    }
    
    if (analysis.importRules > 5) {
      analysis.potentialIssues.push('Many @import rules (consider bundling)');
    }

    if (content.includes('!important')) {
      const importantCount = (content.match(/!important/g) || []).length;
      if (importantCount > 10) {
        analysis.potentialIssues.push(`High usage of !important (${importantCount} occurrences)`);
      }
    }

    return analysis;
  }

  findDuplicates(array) {
    const seen = new Set();
    const duplicates = new Set();
    
    for (const item of array) {
      if (seen.has(item)) {
        duplicates.add(item);
      } else {
        seen.add(item);
      }
    }
    
    return Array.from(duplicates);
  }

  async generateMetrics() {
    const files = this.results.files;
    
    this.results.metrics = {
      totalSizeKB: Math.round(this.results.totalSize / 1024 * 100) / 100,
      averageFileSize: Math.round(this.results.totalSize / files.length / 1024 * 100) / 100,
      largestFile: files[0],
      smallestFile: files[files.length - 1],
      totalSelectors: files.reduce((sum, f) => sum + (f.analysis?.selectors || 0), 0),
      totalDeclarations: files.reduce((sum, f) => sum + (f.analysis?.declarations || 0), 0),
      totalMediaQueries: files.reduce((sum, f) => sum + (f.analysis?.mediaQueries || 0), 0),
      totalCustomProperties: files.reduce((sum, f) => sum + (f.analysis?.customProperties || 0), 0),
      filesWithIssues: files.filter(f => f.analysis?.potentialIssues?.length > 0).length
    };

    // Calculate compression potential
    try {
      const gzipSize = this.estimateGzipSize();
      this.results.metrics.gzipSizeKB = gzipSize;
      this.results.metrics.compressionRatio = Math.round((gzipSize / this.results.metrics.totalSizeKB) * 100);
    } catch (error) {
      console.warn('Could not estimate gzip size:', error.message);
    }
  }

  estimateGzipSize() {
    // Simple estimation: gzip typically compresses CSS to 15-30% of original size
    // This is a rough estimate - actual compression depends on content
    return Math.round(this.results.metrics.totalSizeKB * 0.25 * 100) / 100;
  }

  generateSuggestions() {
    const { metrics, files } = this.results;
    const suggestions = [];

    // File size suggestions
    if (metrics.totalSizeKB > 500) {
      suggestions.push({
        type: 'size',
        severity: 'high',
        message: `Total CSS size (${metrics.totalSizeKB}KB) is quite large. Consider splitting or minifying.`
      });
    }

    if (metrics.largestFile.sizeKB > 100) {
      suggestions.push({
        type: 'size',
        severity: 'medium',
        message: `Largest file (${metrics.largestFile.path}) is ${metrics.largestFile.sizeKB}KB. Consider breaking it down.`
      });
    }

    // Performance suggestions
    const filesWithManyImports = files.filter(f => f.analysis?.importRules > 3);
    if (filesWithManyImports.length > 0) {
      suggestions.push({
        type: 'performance',
        severity: 'medium',
        message: `${filesWithManyImports.length} files have many @import rules. Consider bundling CSS files.`
      });
    }

    // Code quality suggestions
    const duplicateCount = files.reduce((sum, f) => sum + (f.analysis?.duplicateSelectors?.length || 0), 0);
    if (duplicateCount > 0) {
      suggestions.push({
        type: 'quality',
        severity: 'low',
        message: `Found ${duplicateCount} duplicate selectors across files. Consider deduplication.`
      });
    }

    const complexSelectorCount = files.reduce((sum, f) => sum + (f.analysis?.complexSelectors || 0), 0);
    if (complexSelectorCount > metrics.totalSelectors * 0.2) {
      suggestions.push({
        type: 'quality',
        severity: 'low',
        message: `${complexSelectorCount} complex selectors found. Consider simplifying for better performance.`
      });
    }

    // Best practice suggestions
    if (metrics.totalCustomProperties < 10) {
      suggestions.push({
        type: 'best-practice',
        severity: 'info',
        message: 'Consider using more CSS custom properties for better maintainability.'
      });
    }

    this.results.suggestions = suggestions;
  }

  async saveReport() {
    const reportPath = 'css-performance-report.json';
    await fs.writeFile(reportPath, JSON.stringify(this.results, null, 2));
    console.log(`📄 Report saved to ${reportPath}`);
  }

  displayResults() {
    const { metrics, suggestions } = this.results;
    
    console.log('\n🎯 CSS Performance Analysis Results');
    console.log('=====================================');
    console.log(`📁 Total files: ${this.results.totalFiles}`);
    console.log(`📦 Total size: ${metrics.totalSizeKB}KB`);
    console.log(`📊 Average file size: ${metrics.averageFileSize}KB`);
    console.log(`🎯 Estimated gzip size: ${metrics.gzipSizeKB}KB (${metrics.compressionRatio}% compression)`);
    console.log(`🎨 Total selectors: ${metrics.totalSelectors}`);
    console.log(`📝 Total declarations: ${metrics.totalDeclarations}`);
    console.log(`📱 Media queries: ${metrics.totalMediaQueries}`);
    console.log(`🎛️  Custom properties: ${metrics.totalCustomProperties}`);
    
    if (metrics.largestFile) {
      console.log(`\n🔥 Largest file: ${metrics.largestFile.path} (${metrics.largestFile.sizeKB}KB)`);
    }
    
    if (suggestions.length > 0) {
      console.log('\n💡 Suggestions:');
      suggestions.forEach((suggestion, index) => {
        const icon = suggestion.severity === 'high' ? '🔴' : 
                    suggestion.severity === 'medium' ? '🟡' : 
                    suggestion.severity === 'low' ? '🟢' : 'ℹ️';
        console.log(`${icon} ${suggestion.message}`);
      });
    } else {
      console.log('\n✅ No major issues found!');
    }
    
    console.log('\n📈 Performance Score:', this.calculateScore());
  }

  calculateScore() {
    let score = 100;
    const { metrics, suggestions } = this.results;
    
    // Deduct points for issues
    suggestions.forEach(suggestion => {
      switch (suggestion.severity) {
        case 'high': score -= 20; break;
        case 'medium': score -= 10; break;
        case 'low': score -= 5; break;
        default: score -= 2; break;
      }
    });
    
    // Bonus points for good practices
    if (metrics.totalCustomProperties > 20) score += 5;
    if (metrics.averageFileSize < 50) score += 5;
    if (metrics.totalSizeKB < 200) score += 10;
    
    return Math.max(0, Math.min(100, score));
  }

  async walkDirectory(dir) {
    const files = [];
    
    async function scan(currentDir) {
      try {
        const entries = await fs.readdir(currentDir, { withFileTypes: true });
        
        for (const entry of entries) {
          const fullPath = path.join(currentDir, entry.name);
          
          if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
            await scan(fullPath);
          } else if (entry.name.endsWith('.css') && !entry.name.includes('.min.')) {
            files.push(fullPath);
          }
        }
      } catch (error) {
        console.warn(`Could not scan directory ${currentDir}:`, error.message);
      }
    }
    
    await scan(dir);
    return files;
  }
}

// CLI usage
if (require.main === module) {
  const cssDir = process.argv[2] || 'web/static/css';
  const monitor = new CSSPerformanceMonitor(cssDir);
  
  monitor.analyze().catch(error => {
    console.error('❌ Analysis failed:', error);
    process.exit(1);
  });
}

module.exports = CSSPerformanceMonitor;