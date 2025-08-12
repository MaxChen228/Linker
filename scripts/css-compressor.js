#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { glob } = require('glob');

/**
 * CSS Build Compressor
 * 
 * Compresses CSS files using gzip and brotli for production deployment
 * Creates compressed versions alongside original files
 */

class CSSCompressor {
    constructor(options = {}) {
        this.inputDirectory = options.inputDirectory || 'web/static/css';
        this.outputDirectory = options.outputDirectory || 'web/static/css/dist';
        this.enableBrotli = options.enableBrotli !== false;
        this.includePatterns = options.includePatterns || ['**/*.css'];
        this.excludePatterns = options.excludePatterns || ['**/node_modules/**', '**/dist/**'];
        this.compressionLevel = options.compressionLevel || 6;
        this.preserveOriginal = options.preserveOriginal !== false;
        this.createManifest = options.createManifest !== false;
        
        this.stats = {
            processedFiles: 0,
            totalOriginalSize: 0,
            totalGzipSize: 0,
            totalBrotliSize: 0,
            compressionTime: 0,
            errors: []
        };
    }

    /**
     * Compress content using gzip
     */
    async compressGzip(content, level = this.compressionLevel) {
        return new Promise((resolve, reject) => {
            zlib.gzip(content, { level }, (err, compressed) => {
                if (err) reject(err);
                else resolve(compressed);
            });
        });
    }

    /**
     * Compress content using brotli
     */
    async compressBrotli(content) {
        if (!zlib.brotliCompress) {
            console.warn('⚠️  Brotli compression not available in this Node.js version');
            return null;
        }

        return new Promise((resolve, reject) => {
            zlib.brotliCompress(content, {
                params: {
                    [zlib.constants.BROTLI_PARAM_QUALITY]: this.compressionLevel,
                    [zlib.constants.BROTLI_PARAM_SIZE_HINT]: content.length
                }
            }, (err, compressed) => {
                if (err) reject(err);
                else resolve(compressed);
            });
        });
    }

    /**
     * Process a single CSS file
     */
    async processFile(inputPath) {
        const startTime = Date.now();
        const relativePath = path.relative(this.inputDirectory, inputPath);
        const baseName = path.basename(inputPath, '.css');
        const dirName = path.dirname(relativePath);
        
        // Create output directory structure
        const outputDir = path.join(this.outputDirectory, dirName);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        try {
            // Read original file
            const content = fs.readFileSync(inputPath);
            const originalSize = content.length;

            // Copy original file if preserveOriginal is true
            if (this.preserveOriginal) {
                const originalOutput = path.join(outputDir, `${baseName}.css`);
                fs.writeFileSync(originalOutput, content);
            }

            // Compress with gzip
            const gzipCompressed = await this.compressGzip(content);
            const gzipPath = path.join(outputDir, `${baseName}.css.gz`);
            fs.writeFileSync(gzipPath, gzipCompressed);

            let brotliCompressed = null;
            let brotliPath = null;

            // Compress with brotli if enabled
            if (this.enableBrotli) {
                brotliCompressed = await this.compressBrotli(content);
                if (brotliCompressed) {
                    brotliPath = path.join(outputDir, `${baseName}.css.br`);
                    fs.writeFileSync(brotliPath, brotliCompressed);
                }
            }

            // Update statistics
            this.stats.processedFiles++;
            this.stats.totalOriginalSize += originalSize;
            this.stats.totalGzipSize += gzipCompressed.length;
            if (brotliCompressed) {
                this.stats.totalBrotliSize += brotliCompressed.length;
            }

            const processingTime = Date.now() - startTime;
            this.stats.compressionTime += processingTime;

            // Return file info
            return {
                originalPath: relativePath,
                originalSize,
                gzipSize: gzipCompressed.length,
                brotliSize: brotliCompressed ? brotliCompressed.length : null,
                gzipPath: path.relative(process.cwd(), gzipPath),
                brotliPath: brotliPath ? path.relative(process.cwd(), brotliPath) : null,
                processingTime,
                gzipRatio: ((originalSize - gzipCompressed.length) / originalSize * 100).toFixed(2),
                brotliRatio: brotliCompressed 
                    ? ((originalSize - brotliCompressed.length) / originalSize * 100).toFixed(2) 
                    : null
            };

        } catch (error) {
            this.stats.errors.push({ file: relativePath, error: error.message });
            throw error;
        }
    }

    /**
     * Find all CSS files to compress
     */
    async findCSSFiles() {
        const patterns = this.includePatterns.map(pattern => 
            path.join(this.inputDirectory, pattern)
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
     * Compress all CSS files
     */
    async compressAll() {
        console.log('🗜️  Starting CSS compression...');
        const startTime = Date.now();

        // Ensure output directory exists
        if (!fs.existsSync(this.outputDirectory)) {
            fs.mkdirSync(this.outputDirectory, { recursive: true });
        }

        // Find all CSS files
        console.log('🔍 Finding CSS files...');
        const files = await this.findCSSFiles();
        console.log(`📄 Found ${files.length} CSS files to compress`);

        const results = [];

        // Process each file
        for (const file of files) {
            try {
                console.log(`  🗜️  Compressing: ${path.relative(process.cwd(), file)}`);
                const result = await this.processFile(file);
                results.push(result);
                
                // Show progress
                const savings = result.gzipRatio;
                console.log(`    💾 Gzip: ${savings}% smaller`);
                if (result.brotliRatio) {
                    console.log(`    💾 Brotli: ${result.brotliRatio}% smaller`);
                }
            } catch (error) {
                console.error(`❌ Error compressing ${file}:`, error.message);
            }
        }

        this.stats.compressionTime = Date.now() - startTime;

        // Create manifest if requested
        if (this.createManifest) {
            await this.generateManifest(results);
        }

        console.log('✅ Compression complete!');
        return results;
    }

    /**
     * Generate compression manifest
     */
    async generateManifest(results) {
        const manifest = {
            version: '1.0.0',
            timestamp: new Date().toISOString(),
            compressionLevel: this.compressionLevel,
            enableBrotli: this.enableBrotli,
            stats: this.stats,
            files: results.map(result => ({
                original: result.originalPath,
                originalSize: result.originalSize,
                gzip: {
                    path: result.gzipPath,
                    size: result.gzipSize,
                    ratio: result.gzipRatio
                },
                brotli: result.brotliSize ? {
                    path: result.brotliPath,
                    size: result.brotliSize,
                    ratio: result.brotliRatio
                } : null
            }))
        };

        const manifestPath = path.join(this.outputDirectory, 'compression-manifest.json');
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
        console.log(`📄 Compression manifest created: ${manifestPath}`);
    }

    /**
     * Clean output directory
     */
    async clean() {
        if (fs.existsSync(this.outputDirectory)) {
            console.log(`🧹 Cleaning output directory: ${this.outputDirectory}`);
            fs.rmSync(this.outputDirectory, { recursive: true, force: true });
        }
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
     * Print compression statistics
     */
    printStats() {
        console.log('\n📊 Compression Statistics');
        console.log('==========================');
        console.log(`Files processed: ${this.stats.processedFiles}`);
        console.log(`Processing time: ${this.stats.compressionTime}ms`);
        console.log(`Original size: ${this.formatBytes(this.stats.totalOriginalSize)}`);
        console.log(`Gzipped size: ${this.formatBytes(this.stats.totalGzipSize)}`);
        
        if (this.stats.totalBrotliSize > 0) {
            console.log(`Brotli size: ${this.formatBytes(this.stats.totalBrotliSize)}`);
        }

        const gzipSavings = this.stats.totalOriginalSize - this.stats.totalGzipSize;
        const gzipRatio = (gzipSavings / this.stats.totalOriginalSize * 100).toFixed(2);
        console.log(`Gzip savings: ${this.formatBytes(gzipSavings)} (${gzipRatio}%)`);

        if (this.stats.totalBrotliSize > 0) {
            const brotliSavings = this.stats.totalOriginalSize - this.stats.totalBrotliSize;
            const brotliRatio = (brotliSavings / this.stats.totalOriginalSize * 100).toFixed(2);
            console.log(`Brotli savings: ${this.formatBytes(brotliSavings)} (${brotliRatio}%)`);
        }

        if (this.stats.errors.length > 0) {
            console.log(`\n❌ Errors: ${this.stats.errors.length}`);
            this.stats.errors.forEach(error => {
                console.log(`  ${error.file}: ${error.error}`);
            });
        }
    }
}

// CLI Interface
if (require.main === module) {
    const args = process.argv.slice(2);
    const options = {};
    
    // Parse command line arguments
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--input-dir':
                options.inputDirectory = args[++i];
                break;
            case '--output-dir':
                options.outputDirectory = args[++i];
                break;
            case '--compression-level':
                options.compressionLevel = parseInt(args[++i]);
                break;
            case '--no-brotli':
                options.enableBrotli = false;
                break;
            case '--no-original':
                options.preserveOriginal = false;
                break;
            case '--no-manifest':
                options.createManifest = false;
                break;
            case '--clean':
                options.cleanFirst = true;
                break;
            case '--help':
                console.log(`
CSS Compressor

Usage: node css-compressor.js [options]

Options:
  --input-dir <path>       Input CSS directory (default: web/static/css)
  --output-dir <path>      Output directory (default: web/static/css/dist)
  --compression-level <n>  Compression level 1-9 (default: 6)
  --no-brotli              Disable brotli compression
  --no-original            Don't copy original files to output
  --no-manifest            Don't create compression manifest
  --clean                  Clean output directory before compression
  --help                   Show this help message

Examples:
  node css-compressor.js
  node css-compressor.js --compression-level 9 --clean
  node css-compressor.js --input-dir src/css --output-dir build/css
                `);
                process.exit(0);
        }
    }
    
    // Run compression
    (async () => {
        try {
            const compressor = new CSSCompressor(options);
            
            if (options.cleanFirst) {
                await compressor.clean();
            }
            
            await compressor.compressAll();
            compressor.printStats();
        } catch (error) {
            console.error('❌ Compression failed:', error.message);
            process.exit(1);
        }
    })();
}

module.exports = CSSCompressor;