# Node.js Dependencies Explanation

## Why Node.js in a Python Project?

This project primarily uses Python, but includes some Node.js dependencies for specific purposes:

### CSS Processing Tools
- **postcss** & **cssnano**: Used for CSS minification and optimization
- Script location: `scripts/utils/build-css.sh`
- Purpose: Compress CSS files for production deployment

### Browser Testing (Optional)
- **playwright**: Browser automation for E2E testing
- Currently not actively used but available for future testing needs

## Installation

```bash
# Only needed if you want to minify CSS
npm install

# Or remove if not needed
rm package.json package-lock.json
rm -rf node_modules/
```

## Alternative Approach

If you prefer a pure Python solution:
- CSS minification can be done with Python packages like `rcssmin`
- Browser testing can use Selenium instead of Playwright

## Recommendation

Keep these dependencies if:
- You need optimized CSS for production
- You plan to implement browser-based testing

Remove them if:
- You're only doing development work
- File size optimization isn't critical
- You prefer Python-only toolchain