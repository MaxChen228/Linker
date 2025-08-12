module.exports = {
  plugins: [
    require('postcss-combine-duplicated-selectors')({
      removeDuplicatedProperties: true,
      removeDuplicatedValues: true
    }),
    require('postcss-merge-rules'),
    require('postcss-discard-duplicates')
  ]
}