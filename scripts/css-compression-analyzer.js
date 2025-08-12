#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { glob } = require('glob');

/**
 * CSS Compression Analysis Tool
 * 
 * Analyzes CSS file sizes with gzip and brotli compression
 * Provides detailed metrics and optimization recommendations
 */

class CompressionAnalyzer {
    constructor(options = {}) {
        this.cssDirectory = options.cssDirectory || 'web/static/css';
        this.outputDirectory = options.outputDirectory || 'reports/compression';
        this.enableBrotli = options.enableBrotli !== false;
        this.includePatterns = options.includePatterns || ['**/*.css'];
        this.excludePatterns = options.excludePatterns || ['**/node_modules/**', '**/dist/**'];
        
        this.results = {
            files: [],
            summary: {
                totalFiles: 0,
                totalOriginalSize: 0,
                totalGzipSize: 0,
                totalBrotliSize: 0,
                averageGzipRatio: 0,
                averageBrotliRatio: 0
            },
            timestamp: new Date().toISOString(),
            version: '1.0.0'
        };
    }

    /**
     * Compress content using gzip
     */
    async compressGzip(content) {
        return new Promise((resolve, reject) => {
            zlib.gzip(content, { level: 6 }, (err, compressed) => {
                if (err) reject(err);
                else resolve(compressed);
            });
        });
    }

    /**
     * Compress content using brotli (if available)
     */
    async compressBrotli(content) {
        if (!zlib.brotliCompress) {
            console.warn('Brotli compression not available in this Node.js version');
            return null;
        }

        return new Promise((resolve, reject) => {
            zlib.brotliCompress(content, {
                params: {
                    [zlib.constants.BROTLI_PARAM_QUALITY]: 6,
                    [zlib.constants.BROTLI_PARAM_SIZE_HINT]: content.length
                }
            }, (err, compressed) => {
                if (err) reject(err);
                else resolve(compressed);
            });
        });
    }

    /**
     * Analyze a single CSS file
     */
    async analyzeFile(filePath) {
        const content = fs.readFileSync(filePath);
        const originalSize = content.length;
        
        const [gzipCompressed, brotliCompressed] = await Promise.all([
            this.compressGzip(content),
            this.enableBrotli ? this.compressBrotli(content) : null
        ]);

        const gzipSize = gzipCompressed.length;
        const brotliSize = brotliCompressed ? brotliCompressed.length : null;
        
        const relativePath = path.relative(process.cwd(), filePath);
        
        const fileResult = {
            path: relativePath,
            originalSize,
            gzipSize,
            brotliSize,
            gzipRatio: ((originalSize - gzipSize) / originalSize * 100).toFixed(2),
            brotliRatio: brotliSize ? ((originalSize - brotliSize) / originalSize * 100).toFixed(2) : null,
            gzipSavings: originalSize - gzipSize,
            brotliSavings: brotliSize ? originalSize - brotliSize : null,
            category: this.categorizeFile(relativePath),
            recommendations: this.generateFileRecommendations(originalSize, gzipSize, brotliSize)
        };

        return fileResult;
    }

    /**
     * Categorize CSS file by type
     */
    categorizeFile(filePath) {
        if (filePath.includes('design-system/01-tokens')) return 'tokens';
        if (filePath.includes('design-system/02-base')) return 'base';
        if (filePath.includes('design-system/03-components')) return 'components';
        if (filePath.includes('design-system/04-layouts')) return 'layouts';
        if (filePath.includes('pages/')) return 'pages';
        if (filePath.includes('index.css')) return 'index';
        return 'other';
    }

    /**
     * Generate optimization recommendations for a file
     */
    generateFileRecommendations(originalSize, gzipSize, brotliSize) {
        const recommendations = [];
        
        // Size-based recommendations
        if (originalSize > 50000) { // 50KB
            recommendations.push('Large file - consider splitting into smaller modules');
        }
        
        // Compression ratio recommendations
        const gzipRatio = (originalSize - gzipSize) / originalSize;
        if (gzipRatio < 0.6) {
            recommendations.push('Low compression ratio - check for repetitive code');
        }
        
        if (brotliSize) {
            const brotliRatio = (originalSize - brotliSize) / originalSize;
            if (brotliRatio > 0.75) {
                recommendations.push('Excellent brotli compression - prioritize for production');
            }
        }
        
        // Performance recommendations
        if (originalSize > 100000) { // 100KB
            recommendations.push('Consider lazy loading or critical CSS extraction');
        }
        
        return recommendations;
    }

    /**
     * Find all CSS files to analyze
     */
    async findCSSFiles() {
        const patterns = this.includePatterns.map(pattern => 
            path.join(this.cssDirectory, pattern)
        );
        
        const files = [];
        for (const pattern of patterns) {
            const found = await glob(pattern, {
                ignore: this.excludePatterns
            });
            files.push(...found);
        }
        
        return [...new Set(files)]; // Remove duplicates
    }

    /**
     * Analyze all CSS files
     */
    async analyzeAll() {
        console.log('🔍 Finding CSS files...');
        const files = await this.findCSSFiles();
        
        console.log(`📊 Analyzing ${files.length} CSS files...`);
        
        for (const file of files) {
            try {
                console.log(`  📄 Analyzing: ${path.relative(process.cwd(), file)}`);
                const result = await this.analyzeFile(file);
                this.results.files.push(result);
            } catch (error) {
                console.error(`❌ Error analyzing ${file}:`, error.message);
            }
        }
        
        this.calculateSummary();
        await this.generateReports();
        
        console.log('✅ Analysis complete!');
        return this.results;
    }

    /**
     * Calculate summary statistics
     */
    calculateSummary() {
        const { files } = this.results;
        
        this.results.summary.totalFiles = files.length;
        this.results.summary.totalOriginalSize = files.reduce((sum, f) => sum + f.originalSize, 0);
        this.results.summary.totalGzipSize = files.reduce((sum, f) => sum + f.gzipSize, 0);
        this.results.summary.totalBrotliSize = files.reduce((sum, f) => sum + (f.brotliSize || 0), 0);
        
        const gzipRatios = files.map(f => parseFloat(f.gzipRatio));
        this.results.summary.averageGzipRatio = (gzipRatios.reduce((sum, r) => sum + r, 0) / files.length).toFixed(2);
        
        if (this.enableBrotli) {
            const brotliRatios = files.filter(f => f.brotliRatio).map(f => parseFloat(f.brotliRatio));
            this.results.summary.averageBrotliRatio = brotliRatios.length > 0 
                ? (brotliRatios.reduce((sum, r) => sum + r, 0) / brotliRatios.length).toFixed(2)
                : 0;
        }
    }

    /**
     * Generate all report formats
     */
    async generateReports() {
        // Ensure output directory exists
        if (!fs.existsSync(this.outputDirectory)) {
            fs.mkdirSync(this.outputDirectory, { recursive: true });
        }

        // Generate JSON report
        await this.generateJSONReport();
        
        // Generate Markdown report
        await this.generateMarkdownReport();
        
        // Generate comparison table
        await this.generateComparisonTable();
    }

    /**
     * Generate JSON report
     */
    async generateJSONReport() {
        const reportPath = path.join(this.outputDirectory, 'compression-analysis.json');
        fs.writeFileSync(reportPath, JSON.stringify(this.results, null, 2));
        console.log(`📄 JSON report generated: ${reportPath}`);
    }

    /**
     * Generate Markdown report
     */
    async generateMarkdownReport() {
        const { summary, files } = this.results;
        
        let content = `# CSS Compression Analysis Report\n\n`;
        content += `Generated: ${this.results.timestamp}\n\n`;
        
        // Summary section
        content += `## Summary\n\n`;
        content += `- **Total Files**: ${summary.totalFiles}\n`;
        content += `- **Total Original Size**: ${this.formatBytes(summary.totalOriginalSize)}\n`;
        content += `- **Total Gzipped Size**: ${this.formatBytes(summary.totalGzipSize)}\n`;
        if (this.enableBrotli) {
            content += `- **Total Brotli Size**: ${this.formatBytes(summary.totalBrotliSize)}\n`;
        }
        content += `- **Average Gzip Compression**: ${summary.averageGzipRatio}%\n`;
        if (this.enableBrotli) {
            content += `- **Average Brotli Compression**: ${summary.averageBrotliRatio}%\n`;
        }
        content += `\n`;

        // Savings section
        const gzipSavings = summary.totalOriginalSize - summary.totalGzipSize;
        const brotliSavings = summary.totalOriginalSize - summary.totalBrotliSize;
        
        content += `## Compression Savings\n\n`;
        content += `- **Gzip Savings**: ${this.formatBytes(gzipSavings)} (${((gzipSavings / summary.totalOriginalSize) * 100).toFixed(2)}%)\n`;
        if (this.enableBrotli) {
            content += `- **Brotli Savings**: ${this.formatBytes(brotliSavings)} (${((brotliSavings / summary.totalOriginalSize) * 100).toFixed(2)}%)\n`;
        }
        content += `\n`;

        // Category breakdown
        const categories = this.groupByCategory();
        content += `## Breakdown by Category\n\n`;
        content += `| Category | Files | Original Size | Gzipped Size | Compression |\n`;
        content += `|----------|-------|---------------|--------------|-------------|\n`;
        
        Object.entries(categories).forEach(([category, data]) => {
            content += `| ${category} | ${data.count} | ${this.formatBytes(data.originalSize)} | ${this.formatBytes(data.gzipSize)} | ${data.avgCompression}% |\n`;
        });
        content += `\n`;

        // Detailed file analysis
        content += `## Detailed File Analysis\n\n`;
        content += `| File | Original | Gzipped | Brotli | Gzip % | Brotli % |\n`;
        content += `|------|----------|---------|--------|--------|----------|\n`;
        
        files.forEach(file => {
            const brotliCol = file.brotliSize ? this.formatBytes(file.brotliSize) : 'N/A';
            const brotliRatioCol = file.brotliRatio ? `${file.brotliRatio}%` : 'N/A';
            content += `| ${file.path} | ${this.formatBytes(file.originalSize)} | ${this.formatBytes(file.gzipSize)} | ${brotliCol} | ${file.gzipRatio}% | ${brotliRatioCol} |\n`;
        });
        content += `\n`;

        // Recommendations
        content += `## Optimization Recommendations\n\n`;
        const allRecommendations = new Set();
        files.forEach(file => {
            file.recommendations.forEach(rec => allRecommendations.add(rec));
        });
        
        allRecommendations.forEach(rec => {
            content += `- ${rec}\n`;
        });

        const reportPath = path.join(this.outputDirectory, 'compression-analysis.md');
        fs.writeFileSync(reportPath, content);
        console.log(`📄 Markdown report generated: ${reportPath}`);
    }

    /**
     * Generate comparison table
     */
    async generateComparisonTable() {
        const { files } = this.results;
        
        // Sort by original size (largest first)
        const sortedFiles = [...files].sort((a, b) => b.originalSize - a.originalSize);
        
        let content = `# CSS File Size Comparison\n\n`;
        content += `## Transfer Size Analysis\n\n`;
        content += `This table shows the actual transfer sizes when files are served with compression.\n\n`;
        
        content += `| Rank | File | Original | Gzipped | Brotli | Transfer Savings |\n`;
        content += `|------|------|----------|---------|--------|------------------|\n`;
        
        sortedFiles.forEach((file, index) => {
            const brotliCol = file.brotliSize ? this.formatBytes(file.brotliSize) : 'N/A';
            const bestCompressed = file.brotliSize ? Math.min(file.gzipSize, file.brotliSize) : file.gzipSize;
            const transferSavings = ((file.originalSize - bestCompressed) / file.originalSize * 100).toFixed(2);
            
            content += `| ${index + 1} | ${file.path} | ${this.formatBytes(file.originalSize)} | ${this.formatBytes(file.gzipSize)} | ${brotliCol} | ${transferSavings}% |\n`;
        });

        const reportPath = path.join(this.outputDirectory, 'size-comparison.md');
        fs.writeFileSync(reportPath, content);
        console.log(`📄 Size comparison generated: ${reportPath}`);
    }

    /**
     * Group files by category for analysis
     */
    groupByCategory() {
        const categories = {};
        
        this.results.files.forEach(file => {
            const cat = file.category;
            if (!categories[cat]) {
                categories[cat] = {
                    count: 0,
                    originalSize: 0,
                    gzipSize: 0,
                    brotliSize: 0
                };
            }
            
            categories[cat].count++;
            categories[cat].originalSize += file.originalSize;
            categories[cat].gzipSize += file.gzipSize;
            categories[cat].brotliSize += file.brotliSize || 0;
        });
        
        // Calculate average compression for each category
        Object.values(categories).forEach(cat => {
            cat.avgCompression = ((cat.originalSize - cat.gzipSize) / cat.originalSize * 100).toFixed(2);
        });
        
        return categories;
    }

    /**
     * Format bytes to human readable format
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Print console summary
     */
    printSummary() {
        const { summary } = this.results;
        
        console.log('\n📊 Compression Analysis Summary');
        console.log('================================');
        console.log(`Files analyzed: ${summary.totalFiles}`);
        console.log(`Original size: ${this.formatBytes(summary.totalOriginalSize)}`);
        console.log(`Gzipped size: ${this.formatBytes(summary.totalGzipSize)} (${summary.averageGzipRatio}% avg compression)`);
        
        if (this.enableBrotli && summary.totalBrotliSize > 0) {
            console.log(`Brotli size: ${this.formatBytes(summary.totalBrotliSize)} (${summary.averageBrotliRatio}% avg compression)`);
        }
        
        const gzipSavings = summary.totalOriginalSize - summary.totalGzipSize;
        console.log(`\n💾 Transfer savings with gzip: ${this.formatBytes(gzipSavings)}`);
        
        if (this.enableBrotli && summary.totalBrotliSize > 0) {
            const brotliSavings = summary.totalOriginalSize - summary.totalBrotliSize;
            console.log(`💾 Transfer savings with brotli: ${this.formatBytes(brotliSavings)}`);
        }
        
        console.log(`\n📁 Reports generated in: ${this.outputDirectory}`);
    }
}

// CLI Interface
if (require.main === module) {
    const args = process.argv.slice(2);
    const options = {};
    
    // Parse command line arguments
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--css-dir':
                options.cssDirectory = args[++i];
                break;
            case '--output-dir':
                options.outputDirectory = args[++i];
                break;
            case '--no-brotli':
                options.enableBrotli = false;
                break;
            case '--help':
                console.log(`
CSS Compression Analyzer

Usage: node css-compression-analyzer.js [options]

Options:
  --css-dir <path>     CSS directory to analyze (default: web/static/css)
  --output-dir <path>  Output directory for reports (default: reports/compression)
  --no-brotli          Disable brotli compression analysis
  --help               Show this help message

Examples:
  node css-compression-analyzer.js
  node css-compression-analyzer.js --css-dir src/css --output-dir build/reports
  node css-compression-analyzer.js --no-brotli
                `);
                process.exit(0);
        }
    }
    
    // Run analysis
    (async () => {
        try {
            const analyzer = new CompressionAnalyzer(options);
            await analyzer.analyzeAll();
            analyzer.printSummary();
        } catch (error) {
            console.error('❌ Analysis failed:', error.message);
            process.exit(1);
        }
    })();
}

module.exports = CompressionAnalyzer;