/**
 * 統一API端點管理系統
 * TASK-34: 消除硬編碼 - 統一管理所有API端點
 * 
 * 使用方法：
 * import { apiEndpoints } from './config/api-endpoints.js';
 * const url = apiEndpoints.getUrl('confirmKnowledge');
 */

import environment from './environment.js';

/**
 * API端點管理類
 * 提供統一的API端點管理，支援環境檢測和動態URL構建
 */
class ApiEndpointManager {
    constructor() {
        this.baseUrl = this._detectBaseUrl();
        this.version = 'v1'; // API版本，未來可擴展
        
        // 所有API端點的集中定義
        this.endpoints = {
            // ========== 練習相關API ==========
            generateQuestion: '/api/generate-question',
            gradeAnswer: '/api/grade-answer',
            confirmKnowledge: '/api/confirm-knowledge-points',
            
            // ========== 知識點管理API ==========
            knowledge: '/api/knowledge',
            knowledgeDetail: '/api/knowledge/{id}',
            knowledgeRecommendations: '/api/knowledge/recommendations',
            knowledgeBatch: '/api/knowledge/batch',
            knowledgeBatchProgress: '/api/knowledge/batch/{taskId}/progress',
            knowledgeRestore: '/api/knowledge/{id}/restore',
            knowledgeTrashClear: '/api/knowledge/trash/clear',
            knowledgeDailyLimitStatus: '/api/knowledge/daily-limit/status',
            knowledgeDailyLimitConfig: '/api/knowledge/daily-limit/config',
            knowledgeDailyLimitStats: '/api/knowledge/daily-limit/stats',
            knowledgeSaveWithLimit: '/api/knowledge/save-with-limit',
            
            // ========== 日曆相關API ==========
            calendarDay: '/calendar/api/day/{date}',
            calendarCompleteReview: '/calendar/api/complete-review/{pointId}',
            calendarStreakStats: '/calendar/api/stats/streak',
            
            // ========== 模式分析API ==========
            patterns: '/api/patterns',
            
            // ========== 日誌與監控API ==========
            logs: '/api/logs',
            
            // ========== 測試專用API ==========
            testAsync: '/api/test'
        };
        
        // 環境特定配置
        this.config = {
            timeout: 30000, // 30秒超時
            retries: 3, // 重試次數
            isDevelopment: this._isDevelopment()
        };
    }
    
    /**
     * 智能檢測基礎URL
     * 根據環境自動配置正確的基礎URL
     * @returns {string} 基礎URL
     */
    _detectBaseUrl() {
        return environment.getApiBaseUrl();
    }
    
    /**
     * 檢測是否為開發環境
     * @returns {boolean}
     */
    _isDevelopment() {
        return environment.isDevelopment();
    }
    
    /**
     * 獲取完整的API URL
     * @param {string} endpointName - 端點名稱
     * @param {Object} params - URL參數 (用於替換{id}等佔位符)
     * @param {Object} options - 附加選項
     * @returns {string} 完整的API URL
     * @throws {Error} 如果端點名稱不存在
     */
    getUrl(endpointName, params = {}, options = {}) {
        const endpoint = this.endpoints[endpointName];
        if (!endpoint) {
            throw new Error(`未知的API端點: ${endpointName}`);
        }
        
        // 替換URL中的參數佔位符
        let url = endpoint;
        Object.entries(params).forEach(([key, value]) => {
            url = url.replace(`{${key}}`, encodeURIComponent(value));
        });
        
        // 檢查是否還有未替換的參數
        const unreplacedParams = url.match(/{[^}]+}/g);
        if (unreplacedParams) {
            throw new Error(`API端點 ${endpointName} 缺少必要參數: ${unreplacedParams.join(', ')}`);
        }
        
        // 構建完整URL
        const fullUrl = `${this.baseUrl}${url}`;
        
        // 開發環境下的調試日誌
        if (this.config.isDevelopment && options.debug !== false) {
            console.debug(`API URL構建: ${endpointName} -> ${fullUrl}`);
        }
        
        return fullUrl;
    }
    
    /**
     * 批量獲取多個API URL
     * @param {Array} endpoints - 端點配置數組 [{name, params}, ...]
     * @returns {Object} 端點名稱到URL的映射
     */
    getUrls(endpoints) {
        const result = {};
        endpoints.forEach(({ name, params = {} }) => {
            result[name] = this.getUrl(name, params);
        });
        return result;
    }
    
    // ========== 便捷方法 ==========
    
    /**
     * 知識點詳情URL
     * @param {number|string} id - 知識點ID
     * @returns {string}
     */
    knowledgeDetail(id) {
        return this.getUrl('knowledgeDetail', { id });
    }
    
    /**
     * 知識點批次處理進度URL
     * @param {string} taskId - 任務ID
     * @returns {string}
     */
    knowledgeBatchProgress(taskId) {
        return this.getUrl('knowledgeBatchProgress', { taskId });
    }
    
    /**
     * 日曆日期詳情URL
     * @param {string} date - 日期字符串 (YYYY-MM-DD)
     * @returns {string}
     */
    calendarDay(date) {
        return this.getUrl('calendarDay', { date });
    }
    
    /**
     * 完成複習URL
     * @param {number|string} pointId - 知識點ID
     * @returns {string}
     */
    completeReview(pointId) {
        return this.getUrl('calendarCompleteReview', { pointId });
    }
    
    /**
     * 恢復知識點URL
     * @param {number|string} id - 知識點ID
     * @returns {string}
     */
    restoreKnowledge(id) {
        return this.getUrl('knowledgeRestore', { id });
    }
    
    // ========== 配置方法 ==========
    
    /**
     * 獲取API配置
     * @returns {Object} 配置對象
     */
    getConfig() {
        return { ...this.config };
    }
    
    /**
     * 更新配置
     * @param {Object} newConfig - 新配置
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    
    /**
     * 獲取所有可用的端點名稱
     * @returns {Array<string>} 端點名稱列表
     */
    getAvailableEndpoints() {
        return Object.keys(this.endpoints);
    }
    
    /**
     * 檢查端點是否存在
     * @param {string} endpointName - 端點名稱
     * @returns {boolean}
     */
    hasEndpoint(endpointName) {
        return endpointName in this.endpoints;
    }
    
    /**
     * 添加自定義端點
     * @param {string} name - 端點名稱
     * @param {string} path - 端點路徑
     */
    addCustomEndpoint(name, path) {
        this.endpoints[name] = path;
    }
    
    // ========== 調試和開發工具 ==========
    
    /**
     * 打印所有端點配置（開發環境專用）
     */
    debugPrintEndpoints() {
        if (!this.config.isDevelopment) return;
        
        console.group('API端點配置');
        console.log('基礎URL:', this.baseUrl);
        console.log('可用端點:');
        Object.entries(this.endpoints).forEach(([name, path]) => {
            console.log(`  ${name}: ${this.baseUrl}${path}`);
        });
        console.groupEnd();
    }
    
    /**
     * 驗證所有端點的格式
     * @returns {Array} 驗證錯誤列表
     */
    validateEndpoints() {
        const errors = [];
        
        Object.entries(this.endpoints).forEach(([name, path]) => {
            // 檢查路徑是否以/開頭
            if (!path.startsWith('/')) {
                errors.push(`端點 ${name} 的路徑應以/開頭: ${path}`);
            }
            
            // 檢查是否有未配對的大括號
            const openBraces = (path.match(/{/g) || []).length;
            const closeBraces = (path.match(/}/g) || []).length;
            if (openBraces !== closeBraces) {
                errors.push(`端點 ${name} 的參數佔位符不配對: ${path}`);
            }
        });
        
        return errors;
    }
}

// 創建全局實例
export const apiEndpoints = new ApiEndpointManager();

// 開發環境下自動驗證配置
if (apiEndpoints.getConfig().isDevelopment) {
    const errors = apiEndpoints.validateEndpoints();
    if (errors.length > 0) {
        console.warn('API端點配置錯誤:', errors);
    }
}

// 便捷的全局方法（向後兼容）
export const API_ENDPOINTS = apiEndpoints.endpoints;
export const getApiUrl = (name, params) => apiEndpoints.getUrl(name, params);

// TASK-32: 為 settings.js 添加 UPPER_SNAKE_CASE 別名支持
// 這樣 settings.js 可以使用 apiEndpoints.KNOWLEDGE_DAILY_LIMIT_CONFIG 格式
Object.defineProperties(apiEndpoints, {
    'KNOWLEDGE_DAILY_LIMIT_STATUS': {
        get() { return this.getUrl('knowledgeDailyLimitStatus'); },
        enumerable: true
    },
    'KNOWLEDGE_DAILY_LIMIT_CONFIG': {
        get() { return this.getUrl('knowledgeDailyLimitConfig'); },
        enumerable: true
    },
    'KNOWLEDGE_DAILY_LIMIT_STATS': {
        get() { return this.getUrl('knowledgeDailyLimitStats'); },
        enumerable: true
    },
    'KNOWLEDGE_SAVE_WITH_LIMIT': {
        get() { return this.getUrl('knowledgeSaveWithLimit'); },
        enumerable: true
    }
});

// 預設配置常量
export const API_CONFIG = {
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json'
    },
    DEFAULT_TIMEOUT: apiEndpoints.getConfig().timeout
};

// TASK-34: 註冊到全局window對象，供HTML模板內嵌JavaScript使用
// 這樣HTML模板中的script標籤可以通過 window.apiEndpoints 訪問
if (typeof window !== 'undefined') {
    window.apiEndpoints = apiEndpoints;
    
    // 為了向後兼容，也提供簡化的方法
    window.getApiUrl = (name, params) => apiEndpoints.getUrl(name, params);
    
    // 開發環境下的提示
    if (apiEndpoints.getConfig().isDevelopment) {
        console.info('API端點管理器已註冊到window.apiEndpoints');
    }
}