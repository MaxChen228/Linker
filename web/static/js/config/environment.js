/**
 * 統一環境檢測配置
 * 消除localhost/IP硬編碼，提供集中化環境判斷
 * TASK-34: 從API獲取配置，消除端口硬編碼
 */

class EnvironmentDetector {
    constructor() {
        // 開發環境主機名列表（可擴展）
        this.DEV_HOSTNAMES = ['localhost', '127.0.0.1', '0.0.0.0'];
        
        // 開發環境端口列表（將從API獲取，這裡作為默認值）
        this.DEV_PORTS = ['8000', '8001', '3000', '5000'];
        
        // 配置數據（從API獲取）
        this._config = null;
        
        // 快取環境檢測結果
        this._isDev = null;
        this._isProd = null;
        this._isTest = null;
        
        this._detectEnvironment();
        this._loadConfig(); // 異步加載配置
    }
    
    _detectEnvironment() {
        const hostname = window.location.hostname;
        const port = window.location.port;
        const pathname = window.location.pathname;
        
        // 開發環境檢測
        this._isDev = this.DEV_HOSTNAMES.includes(hostname) || 
                      this.DEV_PORTS.includes(port);
        
        // 測試環境檢測（可能包含test或staging關鍵字）
        this._isTest = hostname.includes('test') || 
                       hostname.includes('staging') ||
                       pathname.includes('/test');
        
        // 生產環境（非開發且非測試）
        this._isProd = !this._isDev && !this._isTest;
    }
    
    /**
     * 是否為開發環境
     */
    isDevelopment() {
        return this._isDev;
    }
    
    /**
     * 是否為生產環境
     */
    isProduction() {
        return this._isProd;
    }
    
    /**
     * 是否為測試環境
     */
    isTesting() {
        return this._isTest;
    }
    
    /**
     * 是否為本地環境（localhost或127.0.0.1）
     */
    isLocalhost() {
        const hostname = window.location.hostname;
        return hostname === 'localhost' || hostname === '127.0.0.1';
    }
    
    /**
     * 獲取環境名稱
     */
    getEnvironmentName() {
        if (this._isDev) return 'development';
        if (this._isTest) return 'testing';
        if (this._isProd) return 'production';
        return 'unknown';
    }
    
    /**
     * 異步加載配置
     */
    async _loadConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                this._config = await response.json();
                // 更新開發端口列表
                if (this._config.dev_ports) {
                    this.DEV_PORTS = this._config.dev_ports;
                }
                // 重新檢測環境（因為端口列表可能已更新）
                this._detectEnvironment();
            }
        } catch (error) {
            console.warn('Failed to load config from API, using defaults:', error);
        }
    }
    
    /**
     * 獲取API基礎URL（根據環境自動判斷）
     */
    getApiBaseUrl() {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        // 如果有配置，使用配置中的端口
        if (this._config && this._config.app_port) {
            const configPort = this._config.app_port.toString();
            // 如果當前沒有端口但是配置了端口，使用配置端口
            if (!port && this._isDev) {
                return `${protocol}//${hostname}:${configPort}`;
            }
        }
        
        // 其他環境使用當前URL
        return port ? `${protocol}//${hostname}:${port}` : `${protocol}//${hostname}`;
    }
    
    /**
     * 獲取日誌級別（根據環境自動判斷）
     */
    getLogLevel() {
        if (this._isProd) return 'WARNING';
        if (this._isTest) return 'INFO';
        return 'DEBUG';
    }
    
    /**
     * 檢查是否應該啟用調試功能
     */
    shouldEnableDebug() {
        return this._isDev || this._isTest;
    }
}

// 創建單例實例
const environment = new EnvironmentDetector();

// 導出給其他模組使用
export default environment;
export { 
    environment,
    EnvironmentDetector 
};