/**
 * 統一的前端日誌系統
 * 提供與後端一致的日誌級別和格式
 */

class Logger {
    constructor(moduleName, options = {}) {
        this.moduleName = moduleName;
        this.logLevel = options.logLevel || this.getLogLevel();
        this.enableConsole = options.enableConsole !== false;
        this.enableRemote = options.enableRemote || false;
        this.remoteEndpoint = options.remoteEndpoint || '/api/logs';
        
        // 日誌級別
        this.levels = {
            DEBUG: 10,
            INFO: 20,
            WARNING: 30,
            ERROR: 40,
            CRITICAL: 50
        };
        
        // 顏色配置
        this.colors = {
            DEBUG: '#36a3d9',
            INFO: '#4caf50',
            WARNING: '#ff9800',
            ERROR: '#f44336',
            CRITICAL: '#9c27b0'
        };
        
        // 日誌緩衝（用於批量發送到後端）
        this.logBuffer = [];
        this.bufferSize = options.bufferSize || 10;
        this.flushInterval = options.flushInterval || 5000; // 5秒
        
        // 啟動定時刷新
        if (this.enableRemote) {
            this.startBufferFlush();
        }
    }
    
    getLogLevel() {
        // 從環境或 localStorage 讀取日誌級別
        const stored = localStorage.getItem('logLevel');
        if (stored) return stored;
        
        // 根據環境判斷
        const isProduction = window.location.hostname !== 'localhost' && 
                           window.location.hostname !== '127.0.0.1';
        return isProduction ? 'WARNING' : 'DEBUG';
    }
    
    shouldLog(level) {
        return this.levels[level] >= this.levels[this.logLevel];
    }
    
    formatMessage(level, message, data = {}) {
        const timestamp = new Date().toISOString();
        return {
            timestamp,
            level,
            module: this.moduleName,
            message,
            data,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
    }
    
    log(level, message, data = {}) {
        if (!this.shouldLog(level)) return;
        
        const logEntry = this.formatMessage(level, message, data);
        
        // 輸出到控制台
        if (this.enableConsole) {
            this.consoleLog(level, logEntry);
        }
        
        // 添加到緩衝區
        if (this.enableRemote) {
            this.addToBuffer(logEntry);
        }
        
        return logEntry;
    }
    
    consoleLog(level, logEntry) {
        const color = this.colors[level];
        const style = `color: ${color}; font-weight: bold`;
        const prefix = `%c[${logEntry.timestamp.split('T')[1].split('.')[0]}] [${this.moduleName}] [${level}]`;
        
        // 根據級別使用不同的 console 方法
        const consoleMethod = {
            DEBUG: 'debug',
            INFO: 'log',
            WARNING: 'warn',
            ERROR: 'error',
            CRITICAL: 'error'
        }[level] || 'log';
        
        console[consoleMethod](prefix, style, logEntry.message, logEntry.data);
    }
    
    addToBuffer(logEntry) {
        this.logBuffer.push(logEntry);
        
        // 如果緩衝區滿了，立即發送
        if (this.logBuffer.length >= this.bufferSize) {
            this.flushBuffer();
        }
    }
    
    async flushBuffer() {
        if (this.logBuffer.length === 0) return;
        
        const logs = [...this.logBuffer];
        this.logBuffer = [];
        
        try {
            await fetch(this.remoteEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ logs })
            });
        } catch (error) {
            // 靜默失敗，避免影響主要功能
            console.error('Failed to send logs to server:', error);
        }
    }
    
    startBufferFlush() {
        setInterval(() => {
            this.flushBuffer();
        }, this.flushInterval);
        
        // 頁面卸載時發送剩餘日誌
        window.addEventListener('beforeunload', () => {
            this.flushBuffer();
        });
    }
    
    // 便捷方法
    debug(message, data) {
        return this.log('DEBUG', message, data);
    }
    
    info(message, data) {
        return this.log('INFO', message, data);
    }
    
    warning(message, data) {
        return this.log('WARNING', message, data);
    }
    
    error(message, data) {
        return this.log('ERROR', message, data);
    }
    
    critical(message, data) {
        return this.log('CRITICAL', message, data);
    }
    
    // 特殊日誌方法
    logApiCall(method, url, options = {}, response = null, error = null) {
        const data = {
            method,
            url,
            options: {
                ...options,
                // 移除敏感信息
                headers: this.sanitizeHeaders(options.headers)
            }
        };
        
        if (error) {
            data.error = {
                message: error.message,
                stack: error.stack
            };
            this.error(`API call failed: ${method} ${url}`, data);
        } else {
            data.response = {
                status: response?.status,
                statusText: response?.statusText,
                // 只記錄前 200 字符
                preview: JSON.stringify(response?.data).substring(0, 200)
            };
            this.info(`API call: ${method} ${url}`, data);
        }
    }
    
    logUserAction(action, details = {}) {
        this.info(`User action: ${action}`, {
            action,
            ...details,
            timestamp: Date.now()
        });
    }
    
    logPerformance(operation, startTime, endTime = Date.now()) {
        const duration = endTime - startTime;
        const data = {
            operation,
            duration,
            durationFormatted: `${duration}ms`
        };
        
        if (duration > 1000) {
            this.warning(`Slow operation: ${operation}`, data);
        } else {
            this.debug(`Operation completed: ${operation}`, data);
        }
    }
    
    sanitizeHeaders(headers = {}) {
        const sanitized = {};
        const sensitiveKeys = ['authorization', 'api-key', 'x-api-key', 'cookie'];
        
        for (const [key, value] of Object.entries(headers)) {
            if (sensitiveKeys.some(k => key.toLowerCase().includes(k))) {
                sanitized[key] = '***';
            } else {
                sanitized[key] = value;
            }
        }
        
        return sanitized;
    }
    
    // 設置日誌級別
    setLogLevel(level) {
        if (this.levels[level] !== undefined) {
            this.logLevel = level;
            localStorage.setItem('logLevel', level);
            this.info(`Log level changed to ${level}`);
            return true;
        }
        return false;
    }
}

// 創建全局日誌管理器
class LogManager {
    constructor() {
        this.loggers = {};
        this.defaultOptions = {
            enableConsole: true,
            enableRemote: false, // 預設不發送到後端
            logLevel: null // 使用自動判斷
        };
    }
    
    getLogger(moduleName, options = {}) {
        if (!this.loggers[moduleName]) {
            this.loggers[moduleName] = new Logger(moduleName, {
                ...this.defaultOptions,
                ...options
            });
        }
        return this.loggers[moduleName];
    }
    
    setGlobalLogLevel(level) {
        localStorage.setItem('logLevel', level);
        for (const logger of Object.values(this.loggers)) {
            logger.setLogLevel(level);
        }
    }
    
    enableRemoteLogging(endpoint = '/api/logs') {
        this.defaultOptions.enableRemote = true;
        this.defaultOptions.remoteEndpoint = endpoint;
        
        // 更新現有的 loggers
        for (const logger of Object.values(this.loggers)) {
            logger.enableRemote = true;
            logger.remoteEndpoint = endpoint;
            if (!logger.flushInterval) {
                logger.startBufferFlush();
            }
        }
    }
}

// 創建全局實例
window.LogManager = new LogManager();

// 導出便捷函數
window.getLogger = function(moduleName, options) {
    return window.LogManager.getLogger(moduleName, options);
};

// 預定義的 loggers
window.mainLogger = window.getLogger('main');
window.practiceLogger = window.getLogger('practice');
window.patternsLogger = window.getLogger('patterns');
window.knowledgeLogger = window.getLogger('knowledge');

// 全局錯誤捕獲
window.addEventListener('error', (event) => {
    window.mainLogger.error('Uncaught error', {
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        column: event.colno,
        stack: event.error?.stack
    });
});

window.addEventListener('unhandledrejection', (event) => {
    window.mainLogger.error('Unhandled promise rejection', {
        reason: event.reason,
        promise: event.promise
    });
});

// 開發者工具
window.setLogLevel = function(level) {
    window.LogManager.setGlobalLogLevel(level);
    console.log(`Global log level set to ${level}`);
};

window.enableRemoteLogging = function(endpoint) {
    window.LogManager.enableRemoteLogging(endpoint);
    console.log('Remote logging enabled');
};