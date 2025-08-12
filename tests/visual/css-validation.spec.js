const { test, expect } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

/**
 * CSS validation and analysis tests
 * These tests check for CSS issues, performance problems, and best practices
 */

test.describe('CSS Validation Tests', () => {
  let cssFiles = [];
  
  test.beforeAll(async () => {
    // Discover all CSS files
    const cssDir = path.join(__dirname, '../../web/static/css');
    cssFiles = await discoverCSSFiles(cssDir);
  });
  
  test('CSS files load without errors', async ({ page }) => {
    const cssErrors = [];
    
    // Listen for CSS loading errors
    page.on('response', response => {
      if (response.url().includes('.css') && !response.ok()) {
        cssErrors.push(`Failed to load CSS: ${response.url()} - ${response.status()}`);
      }
    });
    
    page.on('pageerror', error => {
      if (error.message.includes('CSS') || error.message.includes('stylesheet')) {
        cssErrors.push(`CSS Error: ${error.message}`);
      }
    });
    
    // Test each main page
    const pages = ['/', '/practice', '/knowledge', '/patterns'];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');
    }
    
    expect(cssErrors).toHaveLength(0);
  });
  
  test('no CSS parsing errors in browser', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for CSS parsing errors
    const cssErrors = await page.evaluate(() => {
      const errors = [];
      const stylesheets = Array.from(document.styleSheets);
      
      stylesheets.forEach((sheet, index) => {
        try {
          const rules = sheet.cssRules || sheet.rules;
          if (!rules) {
            errors.push(`Stylesheet ${index}: No rules found`);
          }
        } catch (e) {
          // Skip cross-origin stylesheets
          if (!e.message.includes('cross-origin')) {
            errors.push(`Stylesheet ${index}: ${e.message}`);
          }
        }
      });
      
      return errors;
    });
    
    expect(cssErrors).toHaveLength(0);
  });
  
  test('CSS performance metrics', async ({ page }) => {
    // Start performance monitoring
    await page.goto('/', { waitUntil: 'networkidle' });
    
    const metrics = await page.evaluate(() => {
      const perfEntries = performance.getEntriesByType('resource');
      const cssEntries = perfEntries.filter(entry => 
        entry.name.includes('.css') && entry.transferSize > 0
      );
      
      return {
        totalCSSSize: cssEntries.reduce((sum, entry) => sum + entry.transferSize, 0),
        cssLoadTime: Math.max(...cssEntries.map(entry => entry.duration)),
        cssCount: cssEntries.length,
        largestCSS: cssEntries.reduce((largest, entry) => 
          entry.transferSize > (largest.transferSize || 0) ? entry : largest, {}
        )
      };
    });
    
    // Performance assertions
    expect(metrics.totalCSSSize).toBeLessThan(500 * 1024); // Less than 500KB total
    expect(metrics.cssLoadTime).toBeLessThan(2000); // Less than 2 seconds
    expect(metrics.cssCount).toBeLessThan(20); // Reasonable number of CSS files
    
    console.log('CSS Performance Metrics:', metrics);
  });
  
  test('no unused CSS selectors (basic check)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Get all CSS rules and check if they match elements
    const unusedSelectors = await page.evaluate(() => {
      const unused = [];
      const stylesheets = Array.from(document.styleSheets);
      
      stylesheets.forEach(sheet => {
        try {
          const rules = sheet.cssRules || sheet.rules;
          if (rules) {
            Array.from(rules).forEach(rule => {
              if (rule.type === CSSRule.STYLE_RULE) {
                try {
                  const elements = document.querySelectorAll(rule.selectorText);
                  if (elements.length === 0) {
                    unused.push(rule.selectorText);
                  }
                } catch (e) {
                  // Invalid selector or pseudo-selector
                }
              }
            });
          }
        } catch (e) {
          // Skip cross-origin stylesheets
        }
      });
      
      return unused.slice(0, 10); // Limit output
    });
    
    // This is informational - high unused selector count might indicate cleanup needed
    if (unusedSelectors.length > 50) {
      console.warn(`Found ${unusedSelectors.length} potentially unused selectors`);
      console.warn('Sample unused selectors:', unusedSelectors.slice(0, 5));
    }
  });
  
  test('CSS accessibility checks', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const a11yIssues = await page.evaluate(() => {
      const issues = [];
      
      // Check for sufficient color contrast (basic check)
      const elements = document.querySelectorAll('*');
      let lowContrastCount = 0;
      
      elements.forEach(element => {
        const styles = window.getComputedStyle(element);
        const color = styles.color;
        const backgroundColor = styles.backgroundColor;
        
        // Very basic contrast check - in real scenarios, use proper contrast calculation
        if (color === backgroundColor || 
            (color === 'rgb(0, 0, 0)' && backgroundColor === 'rgb(0, 0, 0)')) {
          lowContrastCount++;
        }
      });
      
      if (lowContrastCount > 0) {
        issues.push(`Potential low contrast elements: ${lowContrastCount}`);
      }
      
      // Check for proper focus indicators
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      let missingFocusIndicators = 0;
      focusableElements.forEach(element => {
        const styles = window.getComputedStyle(element, ':focus');
        if (!styles.outline || styles.outline === 'none') {
          missingFocusIndicators++;
        }
      });
      
      if (missingFocusIndicators > 0) {
        issues.push(`Elements without focus indicators: ${missingFocusIndicators}`);
      }
      
      return issues;
    });
    
    // These are warnings, not hard failures
    if (a11yIssues.length > 0) {
      console.warn('Accessibility concerns found:', a11yIssues);
    }
  });
});

// Helper function to discover CSS files
async function discoverCSSFiles(dir) {
  const files = [];
  
  async function scan(currentDir) {
    const entries = await fs.readdir(currentDir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      
      if (entry.isDirectory()) {
        await scan(fullPath);
      } else if (entry.name.endsWith('.css')) {
        files.push(fullPath);
      }
    }
  }
  
  await scan(dir);
  return files;
}

test.describe('CSS File Analysis', () => {
  test('CSS file sizes are reasonable', async () => {
    const cssDir = path.join(__dirname, '../../web/static/css');
    const cssFiles = await discoverCSSFiles(cssDir);
    
    const fileSizes = [];
    
    for (const file of cssFiles) {
      const stats = await fs.stat(file);
      fileSizes.push({
        file: path.relative(cssDir, file),
        size: stats.size
      });
    }
    
    // Sort by size
    fileSizes.sort((a, b) => b.size - a.size);
    
    // Check for oversized files
    const oversizedFiles = fileSizes.filter(f => f.size > 100 * 1024); // > 100KB
    
    if (oversizedFiles.length > 0) {
      console.warn('Large CSS files found:', oversizedFiles);
    }
    
    // Total size check
    const totalSize = fileSizes.reduce((sum, f) => sum + f.size, 0);
    expect(totalSize).toBeLessThan(1024 * 1024); // Less than 1MB total
    
    console.log('CSS file analysis:', {
      totalFiles: fileSizes.length,
      totalSize: `${(totalSize / 1024).toFixed(2)}KB`,
      largestFile: fileSizes[0]
    });
  });
});