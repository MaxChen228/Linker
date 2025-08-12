const { test, expect } = require('@playwright/test');

/**
 * Visual regression tests for key pages
 * These tests capture screenshots and compare them against baseline images
 */

// Test configuration for different viewport sizes
const viewports = [
  { name: 'desktop', width: 1280, height: 720 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 375, height: 667 }
];

// Test pages and their key states
const testPages = [
  {
    name: 'home',
    url: '/',
    description: 'Home page with navigation and main content'
  },
  {
    name: 'practice',
    url: '/practice',
    description: 'Practice page with forms and buttons'
  },
  {
    name: 'knowledge',
    url: '/knowledge',
    description: 'Knowledge points listing page'
  },
  {
    name: 'patterns',
    url: '/patterns',
    description: 'Grammar patterns page'
  }
];

// Helper function to wait for page to be fully loaded
async function waitForPageLoad(page) {
  // Wait for network to be idle
  await page.waitForLoadState('networkidle');
  
  // Wait for any animations to complete
  await page.waitForTimeout(1000);
  
  // Wait for CSS to be applied
  await page.waitForFunction(() => {
    const stylesheets = Array.from(document.styleSheets);
    return stylesheets.every(sheet => {
      try {
        return sheet.cssRules.length > 0;
      } catch (e) {
        return true; // Cross-origin stylesheets
      }
    });
  });
}

// Helper function to hide dynamic content
async function hideDynamicContent(page) {
  // Hide timestamps, random IDs, and other dynamic content
  await page.addStyleTag({
    content: `
      [data-testid="timestamp"],
      .timestamp,
      .dynamic-id,
      .loading-spinner {
        visibility: hidden !important;
      }
      
      /* Disable animations for consistent screenshots */
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `
  });
}

// Generate tests for each page and viewport combination
testPages.forEach(pageConfig => {
  viewports.forEach(viewport => {
    test(`${pageConfig.name} page - ${viewport.name} viewport`, async ({ page }) => {
      // Set viewport size
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // Navigate to page
      await page.goto(pageConfig.url);
      
      // Wait for page to load completely
      await waitForPageLoad(page);
      
      // Hide dynamic content for consistent screenshots
      await hideDynamicContent(page);
      
      // Take full page screenshot
      await expect(page).toHaveScreenshot(`${pageConfig.name}-${viewport.name}-full.png`, {
        fullPage: true,
        clip: null
      });
      
      // Take viewport screenshot
      await expect(page).toHaveScreenshot(`${pageConfig.name}-${viewport.name}-viewport.png`, {
        fullPage: false
      });
    });
  });
});

// Component-specific visual tests
test.describe('Component Visual Tests', () => {
  test('button states', async ({ page }) => {
    await page.goto('/practice');
    await waitForPageLoad(page);
    await hideDynamicContent(page);
    
    // Test different button states
    const buttons = page.locator('button, .btn');
    const count = await buttons.count();
    
    for (let i = 0; i < Math.min(count, 5); i++) {
      const button = buttons.nth(i);
      
      // Normal state
      await expect(button).toHaveScreenshot(`button-${i}-normal.png`);
      
      // Hover state
      await button.hover();
      await expect(button).toHaveScreenshot(`button-${i}-hover.png`);
      
      // Focus state
      await button.focus();
      await expect(button).toHaveScreenshot(`button-${i}-focus.png`);
    }
  });
  
  test('form elements', async ({ page }) => {
    await page.goto('/practice');
    await waitForPageLoad(page);
    await hideDynamicContent(page);
    
    // Test form inputs
    const inputs = page.locator('input, textarea, select');
    const count = await inputs.count();
    
    for (let i = 0; i < Math.min(count, 3); i++) {
      const input = inputs.nth(i);
      
      // Empty state
      await expect(input).toHaveScreenshot(`input-${i}-empty.png`);
      
      // Focused state
      await input.focus();
      await expect(input).toHaveScreenshot(`input-${i}-focused.png`);
      
      // With content
      if (await input.getAttribute('type') !== 'submit') {
        await input.fill('Test content');
        await expect(input).toHaveScreenshot(`input-${i}-filled.png`);
      }
    }
  });
  
  test('card components', async ({ page }) => {
    await page.goto('/knowledge');
    await waitForPageLoad(page);
    await hideDynamicContent(page);
    
    // Test knowledge cards
    const cards = page.locator('.card, .knowledge-card, [class*="card"]');
    const count = await cards.count();
    
    for (let i = 0; i < Math.min(count, 3); i++) {
      const card = cards.nth(i);
      await expect(card).toHaveScreenshot(`card-${i}.png`);
    }
  });
});

// Responsive design tests
test.describe('Responsive Design Tests', () => {
  const breakpoints = [
    { name: 'mobile-small', width: 320, height: 568 },
    { name: 'mobile-medium', width: 375, height: 667 },
    { name: 'mobile-large', width: 414, height: 896 },
    { name: 'tablet-portrait', width: 768, height: 1024 },
    { name: 'tablet-landscape', width: 1024, height: 768 },
    { name: 'desktop-small', width: 1280, height: 720 },
    { name: 'desktop-large', width: 1920, height: 1080 }
  ];
  
  breakpoints.forEach(breakpoint => {
    test(`navigation at ${breakpoint.name}`, async ({ page }) => {
      await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
      await page.goto('/');
      await waitForPageLoad(page);
      await hideDynamicContent(page);
      
      // Screenshot the navigation area
      const nav = page.locator('nav, header, .navigation');
      if (await nav.count() > 0) {
        await expect(nav.first()).toHaveScreenshot(`nav-${breakpoint.name}.png`);
      }
    });
  });
});

// Dark mode / theme tests (if applicable)
test.describe('Theme Tests', () => {
  test('light theme consistency', async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);
    await hideDynamicContent(page);
    
    // Ensure light theme is active
    await page.addStyleTag({
      content: `
        :root {
          color-scheme: light;
        }
        body {
          background: white;
          color: black;
        }
      `
    });
    
    await expect(page).toHaveScreenshot('light-theme-home.png', { fullPage: true });
  });
});