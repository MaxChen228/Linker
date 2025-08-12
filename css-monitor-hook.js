#!/usr/bin/env node

/**
 * CSS Monitoring Pre-commit Hook
 * Runs CSS monitoring and checks for optimization violations
 */

const CSSBuildMonitor = require('./build-monitor.js');
const fs = require('fs');
const path = require('path');

class CSSMonitorHook {
    constructor() {
        this.monitor = new CSSBuildMonitor();
        this.thresholds = {
            maxSizeKB: 1000,           // Maximum total CSS size in KB
            maxHardcodedPixels: 1800,  // Maximum hardcoded pixel values
            maxHardcodedColors: 50,    // Maximum hardcoded color values
            maxImportant: 200,         // Maximum !important usage
            maxFileSizeKB: 400         // Maximum individual file size in KB
        };
    }

    async run() {
        console.log('🔍 Running CSS monitoring pre-commit hook...');
        
        try {
            const metrics = await this.monitor.monitor();
            const violations = this.checkThresholds(metrics);
            
            if (violations.length > 0) {
                console.log('\n❌ CSS Monitoring Violations:');
                violations.forEach((violation, index) => {
                    console.log(`${index + 1}. ${violation.emoji} ${violation.message}`);
                });
                
                console.log('\n💡 Fix these issues before committing or use --no-verify to skip.');
                console.log('📊 Run "npm run css:report" for detailed analysis.');
                
                process.exit(1);
            } else {
                console.log('✅ All CSS monitoring checks passed!');
                this.displaySummary(metrics);
            }
        } catch (error) {
            console.error('❌ CSS monitoring failed:', error.message);
            console.log('⚠️  Skipping CSS monitoring due to error.');
            // Don't fail the commit if monitoring fails
            process.exit(0);
        }
    }

    checkThresholds(metrics) {
        const violations = [];
        const totals = metrics.totals;

        // Check total size
        if (totals.totalSizeKB > this.thresholds.maxSizeKB) {
            violations.push({
                emoji: '🔴',
                message: `Total CSS size (${totals.totalSizeKB}KB) exceeds threshold (${this.thresholds.maxSizeKB}KB)`
            });
        }

        // Check hardcoded pixels
        if (totals.totalHardcodedPixels > this.thresholds.maxHardcodedPixels) {
            violations.push({
                emoji: '🟡',
                message: `Hardcoded pixels (${totals.totalHardcodedPixels}) exceed threshold (${this.thresholds.maxHardcodedPixels})`
            });
        }

        // Check hardcoded colors
        if (totals.totalHardcodedColors > this.thresholds.maxHardcodedColors) {
            violations.push({
                emoji: '🟡',
                message: `Hardcoded colors (${totals.totalHardcodedColors}) exceed threshold (${this.thresholds.maxHardcodedColors})`
            });
        }

        // Check !important usage
        if (totals.totalImportant > this.thresholds.maxImportant) {
            violations.push({
                emoji: '🟠',
                message: `!important usage (${totals.totalImportant}) exceeds threshold (${this.thresholds.maxImportant})`
            });
        }

        // Check individual file sizes
        const largeFiles = metrics.files.filter(file => file.sizeKB > this.thresholds.maxFileSizeKB);
        if (largeFiles.length > 0) {
            largeFiles.forEach(file => {
                violations.push({
                    emoji: '📁',
                    message: `File ${file.filePath} (${file.sizeKB}KB) exceeds size threshold (${this.thresholds.maxFileSizeKB}KB)`
                });
            });
        }

        return violations;
    }

    displaySummary(metrics) {
        const totals = metrics.totals;
        console.log('\n📊 CSS Summary:');
        console.log(`   Size: ${totals.totalSizeKB}KB (${totals.files} files)`);
        console.log(`   Hardcoded: ${totals.totalHardcodedPixels} px, ${totals.totalHardcodedColors} colors`);
        console.log(`   CSS Variables: ${totals.totalCSSVariableUsages} usages`);
        console.log(`   !important: ${totals.totalImportant} instances`);
        
        if (metrics.comparison && !metrics.comparison.isFirstRun) {
            const sizeChange = metrics.comparison.sizeDiffKB;
            const sizeEmoji = sizeChange > 0 ? '📈' : sizeChange < 0 ? '📉' : '➡️';
            console.log(`   Change: ${sizeEmoji} ${sizeChange > 0 ? '+' : ''}${sizeChange}KB since last run`);
        }
    }
}

// CLI interface
if (require.main === module) {
    const hook = new CSSMonitorHook();
    hook.run().catch(console.error);
}

module.exports = CSSMonitorHook;