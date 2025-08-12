/**
 * PurgeCSS Configuration
 * 
 * This configuration removes unused CSS rules from your stylesheets
 * to reduce file sizes in production builds.
 */

module.exports = {
  content: [
    // HTML templates
    'web/templates/**/*.html',
    
    // JavaScript files that may contain dynamic classes
    'web/static/**/*.js',
    'web/static/main.js',
    
    // Python files that may generate classes dynamically
    'web/main.py',
    'core/**/*.py',
    'services/**/*.py'
  ],

  css: [
    // All CSS files in the design system
    'web/static/css/design-system/**/*.css',
    'web/static/css/pages/**/*.css',
    'web/static/css/components.css'
  ],

  // Preserve important classes and patterns
  safelist: {
    // Standard CSS selectors to always keep
    standard: [
      // Base HTML elements
      'html', 'body', 'main', 'header', 'footer', 'nav', 'section', 'article',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li',
      'input', 'textarea', 'button', 'select', 'option', 'form', 'label',
      'table', 'thead', 'tbody', 'tr', 'td', 'th', 'div', 'span', 'img',
      
      // Design system utility classes
      'container', 'stack', 'grid', 'flex', 'hidden', 'visible',
      'text-center', 'text-left', 'text-right',
      'muted', 'brand', 'active',
      
      // Loading and animation classes
      'spinner', 'loading-overlay', 'loading-modal', 'loading-title', 'loading-message',
      'loading-tip', 'loading-tips',
      
      // Modal and overlay classes
      'modal', 'modal-content', 'modal-header', 'modal-body', 'modal-footer',
      'overlay', 'backdrop',
      
      // Form states
      'error', 'success', 'warning', 'info',
      'valid', 'invalid', 'required', 'optional',
      
      // Button variants that might be added dynamically
      'btn-primary', 'btn-secondary', 'btn-ghost', 'btn-gradient',
      'btn-sm', 'btn-md', 'btn-lg', 'btn-xl',
      
      // Badge variants
      'badge-sm', 'badge-md', 'badge-lg',
      
      // Card types
      'card-primary', 'card-secondary', 'card-ghost',
      
      // Practice page specific classes
      'practice-container', 'practice-header', 'practice-subtitle',
      'mode-selection', 'mode-btn', 'answer-section', 'question-section',
      'submit-section', 'practice-ready',
      
      // Queue system classes
      'question-queue', 'queue-header', 'queue-title', 'queue-controls',
      'queue-count', 'queue-items', 'queue-item', 'queue-clear-btn',
      'add-new', 'add-icon',
      
      // Tag system classes
      'tag-selector', 'tag-selector-header', 'tag-selector-title',
      'tag-mode-toggle', 'tag-list', 'tag-item',
      
      // Knowledge system classes
      'knowledge-links', 'point-link', 'review-focus', 'focus-label', 'focus-content',
      
      // Result and grading classes
      'result-section', 'error-analysis', 'error-header', 'error-category-badge',
      'examples', 'zh', 'en',
      
      // Debug modal classes
      'debug-modal', 'debug-modal-content', 'debug-modal-header', 'debug-modal-body',
      'debug-section', 'debug-info', 'info-row', 'info-label', 'info-value',
      'debug-json', 'debug-prompt', 'prompt-container', 'prompt-stats',
      'response-container', 'copy-btn',
      
      // Toast and notification classes
      'generating-toast', 'toast-content', 'show'
    ],

    // Dynamic patterns using regular expressions
    greedy: [
      // Data attributes for CSS styling
      /^data-\w+/,
      
      // Design system tokens
      /^var-\w+/,
      /^token-\w+/,
      
      // Color variations
      /^bg-\w+/,
      /^text-\w+/,
      /^border-\w+/,
      
      // Spacing utilities
      /^m[tblrxy]?-\d+/,
      /^p[tblrxy]?-\d+/,
      /^gap-\d+/,
      /^space-[xy]-\d+/,
      
      // Sizing utilities
      /^w-\d+/,
      /^h-\d+/,
      /^min-w-\d+/,
      /^min-h-\d+/,
      /^max-w-\d+/,
      /^max-h-\d+/,
      
      // Layout utilities
      /^grid-cols-\d+/,
      /^col-span-\d+/,
      /^row-span-\d+/,
      
      // Typography utilities
      /^text-(xs|sm|base|lg|xl|\d+xl)/,
      /^font-(thin|light|normal|medium|semibold|bold|extrabold|black)/,
      /^leading-\w+/,
      /^tracking-\w+/,
      
      // Shadow and effects
      /^shadow-\w+/,
      /^blur-\w+/,
      /^opacity-\d+/,
      
      // Animation classes that may be added dynamically
      /^animate-\w+/,
      /^transition-\w+/,
      /^duration-\d+/,
      /^delay-\d+/,
      
      // Error category badges
      /^error-category-\w+/,
      
      // Question status classes
      /^status-\w+/,
      /^queue-item-\w+/,
      
      // Score display classes
      /^score-(high|medium|low)/,
      
      // Mode indicators
      /^mode-\w+/,
      
      // Interactive states
      /^hover:\w+/,
      /^focus:\w+/,
      /^active:\w+/,
      /^disabled:\w+/,
      
      // Responsive prefixes
      /^sm:\w+/,
      /^md:\w+/,
      /^lg:\w+/,
      /^xl:\w+/,
      /^2xl:\w+/,
      
      // Dark mode variants (if implemented)
      /^dark:\w+/
    ],

    // Deep patterns for nested selectors
    deep: [
      // CSS variables that should be preserved
      /--[\w-]+/,
      
      // Pseudo-selectors
      /:before/,
      /:after/,
      /:hover/,
      /:focus/,
      /:active/,
      /:disabled/,
      /:checked/,
      /:invalid/,
      /:valid/,
      
      // Attribute selectors used in the design system
      /\[data-\w+\]/,
      /\[aria-\w+\]/,
      /\[role="\w+"\]/
    ]
  },

  // Extraction options
  extractors: [
    {
      // Custom extractor for Python templates (Jinja2)
      extractor: content => {
        // Extract class names from various patterns in templates
        const classRegex = /class=["']([^"']*?)["']/g;
        const dataRegex = /data-\w+=/g;
        const conditionalRegex = /\{\%\s*if\s+.*?\%\}(.*?)\{\%\s*endif\s*\%\}/gs;
        
        let classes = [];
        let match;
        
        // Extract class attributes
        while ((match = classRegex.exec(content)) !== null) {
          classes.push(...match[1].split(/\s+/));
        }
        
        // Extract data attributes
        while ((match = dataRegex.exec(content)) !== null) {
          classes.push(match[0]);
        }
        
        // Extract classes from conditional blocks
        while ((match = conditionalRegex.exec(content)) !== null) {
          const innerClassRegex = /class=["']([^"']*?)["']/g;
          let innerMatch;
          while ((innerMatch = innerClassRegex.exec(match[1])) !== null) {
            classes.push(...innerMatch[1].split(/\s+/));
          }
        }
        
        return classes.filter(cls => cls.length > 0);
      },
      extensions: ['html', 'py']
    },
    
    {
      // Custom extractor for JavaScript files
      extractor: content => {
        // Extract class names from JavaScript strings and template literals
        const stringRegex = /['"`]([^'"`]*(?:class|Class)[^'"`]*?)['"`]/g;
        const classNameRegex = /className\s*[:=]\s*['"`]([^'"`]*)['"`]/g;
        const setAttributeRegex = /setAttribute\s*\(\s*['"`]class['"`]\s*,\s*['"`]([^'"`]*)['"`]\s*\)/g;
        const addClassRegex = /(?:add|remove|toggle)Class\s*\(\s*['"`]([^'"`]*)['"`]\s*\)/g;
        
        let classes = [];
        let match;
        
        // Extract from various JavaScript patterns
        const patterns = [stringRegex, classNameRegex, setAttributeRegex, addClassRegex];
        
        patterns.forEach(pattern => {
          while ((match = pattern.exec(content)) !== null) {
            classes.push(...match[1].split(/\s+/));
          }
        });
        
        return classes.filter(cls => cls.length > 0);
      },
      extensions: ['js']
    }
  ],

  // Skip CSS rules that start with these prefixes
  skippedContentGlobs: [
    'node_modules/**',
    'venv/**',
    '**/__pycache__/**',
    '**/.*',
    'css-backups/**',
    'htmlcov/**'
  ],

  // Variables to preserve (CSS custom properties)
  variables: true,

  // Preserve keyframe animations
  keyframes: true,

  // Preserve font-face rules
  fontFace: true,

  // Output options
  rejected: false, // Set to true to see what was removed
  rejectedCss: false // Set to true to output removed CSS to a separate file
};