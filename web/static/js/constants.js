/**
 * API 端點常數
 * 統一管理所有 API 路徑，避免硬編碼
 */

// API 端點常數
export const API_ENDPOINTS = {
    // 練習相關 API
    GENERATE_QUESTION: '/api/generate-question',
    GRADE_ANSWER: '/api/grade-answer',

    // 知識點批次處理 API
    KNOWLEDGE_BATCH: '/api/knowledge/batch',
    KNOWLEDGE_BATCH_PROGRESS: '/api/knowledge/batch',  // 基礎路徑，需要動態添加 taskId

    // 日誌 API
    LOGS: '/api/logs'
};

/**
 * 構建帶有動態參數的 API 路徑
 */
export const API_BUILDERS = {
    /**
     * 構建知識點批次處理進度查詢路徑
     * @param {string} taskId - 任務 ID
     * @returns {string} 完整的 API 路徑
     */
    knowledgeBatchProgress: (taskId) => `${API_ENDPOINTS.KNOWLEDGE_BATCH}/${taskId}/progress`
};

/**
 * API 基礎配置
 */
export const API_CONFIG = {
    // 默認請求配置
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json'
    },

    // 超時設定（毫秒）
    DEFAULT_TIMEOUT: 30000
};
