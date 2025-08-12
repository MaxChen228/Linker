#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

/**
 * CSS Build Monitor
 * Tracks CSS file sizes, optimization metrics, and generates reports
 */
class CSSBuildMonitor {
    constructor() {
        this.cssDir = 'web/static/css';
        this.reportsDir = 'reports/css-monitoring';
        this.metricsFile = path.join(this.reportsDir, 'metrics.json');
        this.currentMetrics = {};
        this.previousMetrics = this.loadPreviousMetrics();
        
        // Ensure reports directory exists
        this.ensureReportsDir();
    }

    ensureReportsDir() {
        if (!fs.existsSync(this.reportsDir)) {
            fs.mkdirSync(this.reportsDir, { recursive: true });
        }
    }

    loadPreviousMetrics() {
        try {
            if (fs.existsSync(this.metricsFile)) {
                return JSON.parse(fs.readFileSync(this.metricsFile, 'utf8'));
            }
        } catch (error) {
            console.warn('Could not load previous metrics:', error.message);
        }
        return null;
    }

    /**
     * Get all CSS files in the project
     */
    getCSSFiles() {
        const pattern = path.join(this.cssDir, '**/*.css');
        return glob.sync(pattern, { absolute: true });
    }

    /**
     * Get file size in bytes
     */
    getFileSize(filePath) {
        try {
            return fs.statSync(filePath).size;
        } catch (error) {
            console.warn(`Could not get size for ${filePath}:`, error.message);
            return 0;
        }
    }

    /**
     * Read CSS file content safely
     */
    readCSSFile(filePath) {
        try {
            return fs.readFileSync(filePath, 'utf8');
        } catch (error) {
            console.warn(`Could not read ${filePath}:`, error.message);
            return '';
        }
    }

    /**
     * Count hardcoded pixel values
     */
    countHardcodedPixels(content) {
        // Match px values but exclude CSS variables and calc() functions
        const pixelRegex = /(?<!var\([^)]*)\b\d+px\b(?![^(]*\))/g;
        const matches = content.match(pixelRegex) || [];
        return {
            count: matches.length,
            values: [...new Set(matches)]
        };
    }

    /**
     * Count hardcoded rgba/rgb values
     */
    countHardcodedColors(content) {
        // Match rgba/rgb but exclude CSS variables
        const colorRegex = /(?<!var\([^)]*)\b(rgba?\([^)]+\)|#[0-9a-fA-F]{3,8})\b(?![^(]*\))/g;
        const matches = content.match(colorRegex) || [];
        return {
            count: matches.length,
            values: [...new Set(matches)]
        };
    }

    /**
     * Count CSS variable usage
     */
    countCSSVariables(content) {
        const varRegex = /var\(--[^)]+\)/g;
        const defineRegex = /--[a-zA-Z][a-zA-Z0-9-]*\s*:/g;
        
        const usages = content.match(varRegex) || [];
        const definitions = content.match(defineRegex) || [];
        
        return {
            usages: usages.length,
            definitions: definitions.length,
            uniqueUsages: [...new Set(usages.map(u => u.match(/--[^,)]+/)[0]))],
            uniqueDefinitions: [...new Set(definitions.map(d => d.replace(/\s*:$/, '')))]
        };
    }

    /**
     * Count !important usage
     */
    countImportant(content) {
        const importantRegex = /!important/g;
        const matches = content.match(importantRegex) || [];
        return matches.length;
    }

    /**
     * Count media queries
     */
    countMediaQueries(content) {
        const mediaRegex = /@media[^{]+{/g;
        const matches = content.match(mediaRegex) || [];
        return {
            count: matches.length,
            queries: [...new Set(matches.map(m => m.replace('{', '').trim()))]
        };
    }

    /**
     * Count CSS rules and selectors
     */
    countRulesAndSelectors(content) {
        // Remove comments and strings to avoid false matches
        const cleanContent = content
            .replace(/\/\*[\s\S]*?\*\//g, '')
            .replace(/"[^"]*"/g, '""')
            .replace(/'[^']*'/g, "''");

        // Count CSS rules (blocks with {})
        const ruleRegex = /[^{}]*{[^{}]*}/g;
        const rules = cleanContent.match(ruleRegex) || [];
        
        // Count selectors (approximate)
        const selectorRegex = /[^{}]+(?={)/g;
        const selectors = cleanContent.match(selectorRegex) || [];
        
        return {
            rules: rules.length,
            selectors: selectors.length
        };
    }

    /**
     * Analyze a single CSS file
     */
    analyzeCSSFile(filePath) {
        const content = this.readCSSFile(filePath);
        const size = this.getFileSize(filePath);
        const relativePath = path.relative(process.cwd(), filePath);

        const hardcodedPixels = this.countHardcodedPixels(content);
        const hardcodedColors = this.countHardcodedColors(content);
        const cssVariables = this.countCSSVariables(content);
        const importantCount = this.countImportant(content);
        const mediaQueries = this.countMediaQueries(content);
        const rulesAndSelectors = this.countRulesAndSelectors(content);

        return {
            filePath: relativePath,
            size,
            sizeKB: Math.round(size / 1024 * 100) / 100,
            lines: content.split('\n').length,
            hardcodedPixels,
            hardcodedColors,
            cssVariables,
            importantCount,
            mediaQueries,
            rulesAndSelectors,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Calculate total metrics
     */
    calculateTotalMetrics(fileMetrics) {
        const total = {
            files: fileMetrics.length,
            totalSize: 0,
            totalSizeKB: 0,
            totalLines: 0,
            totalHardcodedPixels: 0,
            totalHardcodedColors: 0,
            totalCSSVariableUsages: 0,
            totalCSSVariableDefinitions: 0,
            totalImportant: 0,
            totalMediaQueries: 0,
            totalRules: 0,
            totalSelectors: 0,
            uniquePixelValues: new Set(),
            uniqueColorValues: new Set(),
            uniqueCSSVariables: new Set(),
            uniqueMediaQueries: new Set()
        };

        fileMetrics.forEach(file => {
            total.totalSize += file.size;
            total.totalLines += file.lines;
            total.totalHardcodedPixels += file.hardcodedPixels.count;
            total.totalHardcodedColors += file.hardcodedColors.count;
            total.totalCSSVariableUsages += file.cssVariables.usages;
            total.totalCSSVariableDefinitions += file.cssVariables.definitions;
            total.totalImportant += file.importantCount;
            total.totalMediaQueries += file.mediaQueries.count;
            total.totalRules += file.rulesAndSelectors.rules;
            total.totalSelectors += file.rulesAndSelectors.selectors;

            // Collect unique values
            file.hardcodedPixels.values.forEach(v => total.uniquePixelValues.add(v));
            file.hardcodedColors.values.forEach(v => total.uniqueColorValues.add(v));
            file.cssVariables.uniqueUsages.forEach(v => total.uniqueCSSVariables.add(v));
            file.mediaQueries.queries.forEach(v => total.uniqueMediaQueries.add(v));
        });

        total.totalSizeKB = Math.round(total.totalSize / 1024 * 100) / 100;

        // Convert sets to arrays for JSON serialization
        total.uniquePixelValues = [...total.uniquePixelValues];
        total.uniqueColorValues = [...total.uniqueColorValues];
        total.uniqueCSSVariables = [...total.uniqueCSSVariables];
        total.uniqueMediaQueries = [...total.uniqueMediaQueries];

        return total;
    }

    /**
     * Compare with previous metrics
     */
    compareMetrics(current, previous) {
        if (!previous) {
            return {
                isFirstRun: true,
                message: 'First monitoring run - no comparison available'
            };
        }

        const comparison = {
            isFirstRun: false,
            sizeDiff: current.totals.totalSize - previous.totals.totalSize,
            sizeDiffKB: Math.round((current.totals.totalSize - previous.totals.totalSize) / 1024 * 100) / 100,
            hardcodedPixelsDiff: current.totals.totalHardcodedPixels - previous.totals.totalHardcodedPixels,
            hardcodedColorsDiff: current.totals.totalHardcodedColors - previous.totals.totalHardcodedColors,
            cssVariableUsagesDiff: current.totals.totalCSSVariableUsages - previous.totals.totalCSSVariableUsages,
            importantDiff: current.totals.totalImportant - previous.totals.totalImportant,
            previousTimestamp: previous.timestamp,
            currentTimestamp: current.timestamp
        };

        // Add percentage changes
        if (previous.totals.totalSize > 0) {
            comparison.sizeChangePercent = Math.round((comparison.sizeDiff / previous.totals.totalSize) * 10000) / 100;
        }

        return comparison;
    }

    /**
     * Generate optimization suggestions
     */
    generateOptimizationSuggestions(metrics) {
        const suggestions = [];

        // Size-based suggestions
        if (metrics.totals.totalSizeKB > 500) {
            suggestions.push({
                type: 'size',
                severity: 'high',
                message: `Total CSS size is ${metrics.totals.totalSizeKB}KB. Consider splitting into smaller files or removing unused styles.`
            });
        }

        // Hardcoded values suggestions
        if (metrics.totals.totalHardcodedPixels > 50) {
            suggestions.push({
                type: 'maintainability',
                severity: 'medium',
                message: `Found ${metrics.totals.totalHardcodedPixels} hardcoded pixel values. Consider using CSS variables for spacing.`
            });
        }

        if (metrics.totals.totalHardcodedColors > 20) {
            suggestions.push({
                type: 'maintainability',
                severity: 'medium',
                message: `Found ${metrics.totals.totalHardcodedColors} hardcoded color values. Consider using CSS custom properties for colors.`
            });
        }

        // !important usage
        if (metrics.totals.totalImportant > 10) {
            suggestions.push({
                type: 'specificity',
                severity: 'medium',
                message: `Found ${metrics.totals.totalImportant} !important declarations. Review CSS specificity structure.`
            });
        }

        // CSS variables adoption
        const variableUsageRatio = metrics.totals.totalCSSVariableUsages / (metrics.totals.totalHardcodedPixels + metrics.totals.totalHardcodedColors + 1);
        if (variableUsageRatio < 1) {
            suggestions.push({
                type: 'adoption',
                severity: 'low',
                message: 'CSS variable usage could be increased to improve maintainability.'
            });
        }

        return suggestions;
    }

    /**
     * Main monitoring function
     */
    async monitor() {
        console.log('🔍 Starting CSS monitoring...');
        
        const cssFiles = this.getCSSFiles();
        console.log(`📁 Found ${cssFiles.length} CSS files`);

        const fileMetrics = cssFiles.map(file => this.analyzeCSSFile(file));
        const totals = this.calculateTotalMetrics(fileMetrics);
        
        this.currentMetrics = {
            timestamp: new Date().toISOString(),
            totals,
            files: fileMetrics,
            suggestions: this.generateOptimizationSuggestions({ totals })
        };

        // Compare with previous run
        const comparison = this.compareMetrics(this.currentMetrics, this.previousMetrics);
        this.currentMetrics.comparison = comparison;

        // Save metrics
        this.saveMetrics();
        
        // Generate reports
        this.generateReports();

        console.log('✅ CSS monitoring completed');
        console.log(`📊 Total CSS size: ${totals.totalSizeKB}KB`);
        console.log(`🎯 Hardcoded values: ${totals.totalHardcodedPixels} px, ${totals.totalHardcodedColors} colors`);
        console.log(`🔧 CSS variables: ${totals.totalCSSVariableUsages} usages, ${totals.totalCSSVariableDefinitions} definitions`);
        console.log(`⚠️  !important count: ${totals.totalImportant}`);
        
        if (comparison.sizeDiffKB !== undefined) {
            const sizeChange = comparison.sizeDiffKB > 0 ? `+${comparison.sizeDiffKB}` : comparison.sizeDiffKB;
            console.log(`📈 Size change: ${sizeChange}KB since last run`);
        }

        return this.currentMetrics;
    }

    /**
     * Save metrics to file
     */
    saveMetrics() {
        try {
            fs.writeFileSync(this.metricsFile, JSON.stringify(this.currentMetrics, null, 2));
            console.log(`💾 Metrics saved to ${this.metricsFile}`);
        } catch (error) {
            console.error('Failed to save metrics:', error.message);
        }
    }

    /**
     * Generate detailed reports
     */
    generateReports() {
        // Generate summary report
        this.generateSummaryReport();
        
        // Generate detailed file report
        this.generateDetailedReport();
        
        // Generate trends report (if previous data exists)
        if (this.previousMetrics) {
            this.generateTrendsReport();
        }
    }

    generateSummaryReport() {
        const reportPath = path.join(this.reportsDir, 'summary.md');
        const { totals, comparison, suggestions } = this.currentMetrics;
        
        let content = `# CSS Monitoring Summary\n\n`;
        content += `**Generated:** ${new Date().toLocaleString()}\n\n`;
        
        content += `## Overview\n\n`;
        content += `| Metric | Value |\n`;
        content += `|--------|-------|\n`;
        content += `| Total Files | ${totals.files} |\n`;
        content += `| Total Size | ${totals.totalSizeKB}KB (${totals.totalSize} bytes) |\n`;
        content += `| Total Lines | ${totals.totalLines.toLocaleString()} |\n`;
        content += `| CSS Rules | ${totals.totalRules.toLocaleString()} |\n`;
        content += `| CSS Selectors | ${totals.totalSelectors.toLocaleString()} |\n\n`;
        
        content += `## Code Quality Metrics\n\n`;
        content += `| Metric | Count | Unique Values |\n`;
        content += `|--------|-------|---------------|\n`;
        content += `| Hardcoded Pixels | ${totals.totalHardcodedPixels} | ${totals.uniquePixelValues.length} |\n`;
        content += `| Hardcoded Colors | ${totals.totalHardcodedColors} | ${totals.uniqueColorValues.length} |\n`;
        content += `| CSS Variable Usage | ${totals.totalCSSVariableUsages} | ${totals.uniqueCSSVariables.length} |\n`;
        content += `| CSS Variable Definitions | ${totals.totalCSSVariableDefinitions} | - |\n`;
        content += `| !important Usage | ${totals.totalImportant} | - |\n`;
        content += `| Media Queries | ${totals.totalMediaQueries} | ${totals.uniqueMediaQueries.length} |\n\n`;

        if (!comparison.isFirstRun) {
            content += `## Changes Since Last Run\n\n`;
            content += `- **Size Change:** ${comparison.sizeDiffKB > 0 ? '+' : ''}${comparison.sizeDiffKB}KB\n`;
            content += `- **Hardcoded Pixels:** ${comparison.hardcodedPixelsDiff > 0 ? '+' : ''}${comparison.hardcodedPixelsDiff}\n`;
            content += `- **Hardcoded Colors:** ${comparison.hardcodedColorsDiff > 0 ? '+' : ''}${comparison.hardcodedColorsDiff}\n`;
            content += `- **CSS Variables:** ${comparison.cssVariableUsagesDiff > 0 ? '+' : ''}${comparison.cssVariableUsagesDiff}\n`;
            content += `- **!important:** ${comparison.importantDiff > 0 ? '+' : ''}${comparison.importantDiff}\n\n`;
        }

        if (suggestions.length > 0) {
            content += `## Optimization Suggestions\n\n`;
            suggestions.forEach((suggestion, index) => {
                const emoji = suggestion.severity === 'high' ? '🔴' : suggestion.severity === 'medium' ? '🟡' : '🟢';
                content += `${index + 1}. ${emoji} **${suggestion.type.toUpperCase()}:** ${suggestion.message}\n`;
            });
            content += '\n';
        }

        content += `## Top Largest Files\n\n`;
        const largestFiles = [...this.currentMetrics.files]
            .sort((a, b) => b.size - a.size)
            .slice(0, 10);
        
        content += `| File | Size (KB) | Lines | Hardcoded Pixels | CSS Variables |\n`;
        content += `|------|-----------|-------|------------------|---------------|\n`;
        largestFiles.forEach(file => {
            content += `| ${file.filePath} | ${file.sizeKB} | ${file.lines} | ${file.hardcodedPixels.count} | ${file.cssVariables.usages} |\n`;
        });

        fs.writeFileSync(reportPath, content);
        console.log(`📋 Summary report generated: ${reportPath}`);
    }

    generateDetailedReport() {
        const reportPath = path.join(this.reportsDir, 'detailed.json');
        fs.writeFileSync(reportPath, JSON.stringify(this.currentMetrics, null, 2));
        console.log(`📄 Detailed report generated: ${reportPath}`);
    }

    generateTrendsReport() {
        const reportPath = path.join(this.reportsDir, 'trends.json');
        let trends = [];
        
        // Load existing trends
        try {
            if (fs.existsSync(reportPath)) {
                trends = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            }
        } catch (error) {
            console.warn('Could not load existing trends:', error.message);
        }

        // Add current data point
        trends.push({
            timestamp: this.currentMetrics.timestamp,
            totalSize: this.currentMetrics.totals.totalSize,
            totalSizeKB: this.currentMetrics.totals.totalSizeKB,
            hardcodedPixels: this.currentMetrics.totals.totalHardcodedPixels,
            hardcodedColors: this.currentMetrics.totals.totalHardcodedColors,
            cssVariables: this.currentMetrics.totals.totalCSSVariableUsages,
            important: this.currentMetrics.totals.totalImportant,
            files: this.currentMetrics.totals.files
        });

        // Keep only last 50 data points
        if (trends.length > 50) {
            trends = trends.slice(-50);
        }

        fs.writeFileSync(reportPath, JSON.stringify(trends, null, 2));
        console.log(`📈 Trends report updated: ${reportPath}`);
    }

    /**
     * Monitor changes with file watching
     */
    watch() {
        console.log('👀 Starting CSS file watcher...');
        
        const chokidar = require('chokidar');
        const watcher = chokidar.watch(path.join(this.cssDir, '**/*.css'));
        
        let changeTimeout;
        
        watcher.on('change', (filePath) => {
            console.log(`📝 CSS file changed: ${filePath}`);
            
            // Debounce changes
            clearTimeout(changeTimeout);
            changeTimeout = setTimeout(() => {
                this.monitor();
            }, 1000);
        });
        
        watcher.on('add', (filePath) => {
            console.log(`➕ CSS file added: ${filePath}`);
            this.monitor();
        });
        
        watcher.on('unlink', (filePath) => {
            console.log(`➖ CSS file removed: ${filePath}`);
            this.monitor();
        });
        
        console.log('✅ CSS file watcher started. Press Ctrl+C to stop.');
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2] || 'monitor';
    const monitor = new CSSBuildMonitor();

    switch (command) {
        case 'monitor':
        case 'run':
            monitor.monitor().catch(console.error);
            break;
        case 'watch':
            monitor.watch();
            break;
        case 'help':
            console.log(`
CSS Build Monitor

Usage:
  node build-monitor.js [command]

Commands:
  monitor, run    Run monitoring once (default)
  watch          Watch for file changes and auto-monitor
  help           Show this help message

Examples:
  node build-monitor.js            # Run monitoring once
  node build-monitor.js monitor    # Same as above
  node build-monitor.js watch      # Start file watcher
            `);
            break;
        default:
            console.error(`Unknown command: ${command}`);
            console.log('Run "node build-monitor.js help" for usage information.');
            process.exit(1);
    }
}

module.exports = CSSBuildMonitor;