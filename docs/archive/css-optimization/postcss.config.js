const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  plugins: [
    // First, combine and optimize existing CSS
    require('postcss-combine-duplicated-selectors')({
      removeDuplicatedProperties: true,
      removeDuplicatedValues: true
    }),
    require('postcss-merge-rules'),
    require('postcss-discard-duplicates'),
    
    // Then apply PurgeCSS in production to remove unused styles
    ...(isProduction ? [
      require('@fullhuman/postcss-purgecss').default({
        content: [
          'web/templates/**/*.html',
          'web/static/**/*.js',
          'web/static/main.js',
          'web/main.py',
          'core/**/*.py',
          'services/**/*.py'
        ],
        safelist: {
          standard: [
            // Base HTML elements
            'html', 'body', 'main', 'header', 'footer', 'nav', 'section', 'article',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li',
            'input', 'textarea', 'button', 'select', 'option', 'form', 'label',
            'table', 'thead', 'tbody', 'tr', 'td', 'th', 'div', 'span', 'img', 'small',
            
            // Design system utility classes
            'container', 'stack', 'grid', 'flex', 'hidden', 'visible',
            'text-center', 'text-left', 'text-right',
            'muted', 'brand', 'active', 'list', 'item', 'title',
            
            // Loading and animation classes
            'spinner', 'spinner-ring', 'spinner-container',
            'loading-overlay', 'loading-modal', 'loading-title', 'loading-message',
            'loading-tip', 'loading-tips',
            
            // Modal and overlay classes
            'modal', 'modal-content', 'modal-header', 'modal-body', 'modal-footer',
            'overlay', 'backdrop', 'close-btn',
            
            // Form states and validation
            'error', 'success', 'warning', 'info',
            'valid', 'invalid', 'required', 'optional',
            
            // Common component classes found in templates
            'btn', 'btn-text', 'card', 'badge', 'stat', 'stat-item', 'stat-value', 'stat-label', 'stat-card',
            'sentence-label', 'sentence-text', 'label', 'example', 'variation-item',
            'mastery-fill', 'hint-icon', 'add-icon', 'examples', 'zh', 'en',
            
            // Practice page specific classes
            'practice-container', 'practice-header', 'practice-subtitle',
            'mode-selection', 'mode-btn', 'answer-section', 'question-section',
            'submit-section', 'practice-ready', 'answer-input', 'answer-label',
            'question-content', 'question-label', 'label-text', 'mode-indicator',
            'question-hint', 'hint-text', 'review-focus', 'focus-label', 'focus-content',
            
            // Queue system classes
            'question-queue', 'queue-header', 'queue-title', 'queue-controls',
            'queue-count', 'queue-items', 'queue-item', 'queue-clear-btn',
            'queue-item-header', 'queue-item-body', 'queue-item-footer',
            'queue-item-text', 'queue-item-meta', 'queue-item-badge', 'queue-item-spinner',
            'queue-item-progress', 'progress-bar', 'score-display',
            'add-new', 'add-icon', 'ready', 'active', 'grading', 'completed',
            
            // Tag system classes
            'tag-selector', 'tag-selector-header', 'tag-selector-title',
            'tag-mode-toggle', 'tag-list', 'tag-item',
            
            // Knowledge system classes
            'knowledge-links', 'point-link', 'error-analysis', 'error-header',
            'error-category-badge', 'systematic', 'isolated', 'enhancement', 'other',
            
            // Result and grading classes
            'result-section', 'high', 'medium', 'low',
            
            // Debug modal classes
            'debug-modal', 'debug-modal-content', 'debug-modal-header', 'debug-modal-body',
            'debug-section', 'debug-info', 'info-row', 'info-label', 'info-value',
            'debug-json', 'debug-prompt', 'prompt-container', 'prompt-stats',
            'response-container', 'copy-btn',
            
            // Toast and notification classes
            'generating-toast', 'toast-content', 'show', 'params-row', 'param-group'
          ],
          
          greedy: [
            // Data attributes for CSS styling
            /^data-/,
            
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
            
            // Interactive states
            /^hover:/,
            /^focus:/,
            /^active:/,
            /^disabled:/,
            
            // Responsive prefixes
            /^sm:/,
            /^md:/,
            /^lg:/,
            /^xl:/,
            /^2xl:/,
            
            // Animation and transition classes
            /^animate-/,
            /^transition-/,
            /^duration-/,
            /^delay-/
          ],
          
          deep: [
            // CSS variables
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
            
            // Attribute selectors
            /\[data-\w+\]/,
            /\[aria-\w+\]/,
            /\[role=/
          ]
        },
        variables: true,
        keyframes: true,
        fontFace: true
      })
    ] : []),
    
    // Finally apply cssnano for production optimization
    ...(isProduction ? [
      require('cssnano')({
        preset: ['default', {
          discardComments: { removeAll: true },
          normalizeWhitespace: true,
          minifySelectors: true
        }]
      })
    ] : [])
  ]
}