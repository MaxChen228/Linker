module.exports = {
  plugins: [
    require('cssnano')({
      preset: ['default', {
        discardComments: {
          removeAll: true,
        },
        normalizeWhitespace: true,
        colormin: true,
        reduceIdents: false, // Preserve identifiers for debugging
        zindex: false, // Don't rebase z-index values
        calc: false, // Keep calc() for CSS variables
      }]
    })
  ]
}