/**
 * 練習佇列持久化管理
 * 使用 sessionStorage 保存題目佇列，避免頁面切換時丟失
 */

class QueuePersistence {
  constructor() {
    this.STORAGE_KEY = 'practice_queue';
    this.CURRENT_KEY = 'current_question_id';
    this.EXPIRY_TIME = 2 * 60 * 60 * 1000; // 2小時過期
  }
  
  /**
   * 保存佇列到 sessionStorage
   */
  saveQueue(queue) {
    try {
      const data = {
        queue: queue,
        timestamp: Date.now(),
        version: '1.0'
      };
      sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      console.log('[QueuePersistence] Saved queue with', queue.length, 'items');
    } catch (error) {
      console.error('[QueuePersistence] Failed to save queue:', error);
      // 如果 sessionStorage 滿了，清理舊資料
      if (error.name === 'QuotaExceededError') {
        this.clearOldData();
        try {
          sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
        } catch (retryError) {
          console.error('[QueuePersistence] Still failed after cleanup:', retryError);
        }
      }
    }
  }
  
  /**
   * 從 sessionStorage 載入佇列
   */
  loadQueue() {
    try {
      const dataStr = sessionStorage.getItem(this.STORAGE_KEY);
      if (!dataStr) {
        console.log('[QueuePersistence] No saved queue found');
        return null;
      }
      
      const data = JSON.parse(dataStr);
      
      // 檢查資料版本
      if (data.version !== '1.0') {
        console.warn('[QueuePersistence] Version mismatch, clearing old data');
        this.clearQueue();
        return null;
      }
      
      // 檢查是否過期
      const age = Date.now() - data.timestamp;
      if (age > this.EXPIRY_TIME) {
        console.log('[QueuePersistence] Queue expired, clearing');
        this.clearQueue();
        return null;
      }
      
      console.log('[QueuePersistence] Loaded queue with', data.queue.length, 'items');
      return data.queue;
    } catch (error) {
      console.error('[QueuePersistence] Failed to load queue:', error);
      this.clearQueue();
      return null;
    }
  }
  
  /**
   * 保存當前題目 ID
   */
  saveCurrentQuestion(questionId) {
    try {
      sessionStorage.setItem(this.CURRENT_KEY, questionId);
    } catch (error) {
      console.error('[QueuePersistence] Failed to save current question:', error);
    }
  }
  
  /**
   * 載入當前題目 ID
   */
  loadCurrentQuestion() {
    try {
      return sessionStorage.getItem(this.CURRENT_KEY);
    } catch (error) {
      console.error('[QueuePersistence] Failed to load current question:', error);
      return null;
    }
  }
  
  /**
   * 清除佇列資料
   */
  clearQueue() {
    try {
      sessionStorage.removeItem(this.STORAGE_KEY);
      sessionStorage.removeItem(this.CURRENT_KEY);
      console.log('[QueuePersistence] Queue cleared');
    } catch (error) {
      console.error('[QueuePersistence] Failed to clear queue:', error);
    }
  }
  
  /**
   * 清理舊資料（當儲存空間不足時）
   */
  clearOldData() {
    console.log('[QueuePersistence] Clearing old data to free space');
    const keysToKeep = [this.STORAGE_KEY, this.CURRENT_KEY, 'taggedPractice'];
    const keys = Object.keys(sessionStorage);
    
    keys.forEach(key => {
      if (!keysToKeep.includes(key)) {
        sessionStorage.removeItem(key);
      }
    });
  }
  
  /**
   * 更新佇列中的特定題目
   */
  updateQuestion(questionId, updates) {
    const queue = this.loadQueue();
    if (!queue) return;
    
    const index = queue.findIndex(q => q.id === questionId);
    if (index !== -1) {
      queue[index] = { ...queue[index], ...updates };
      this.saveQueue(queue);
      console.log('[QueuePersistence] Updated question:', questionId);
    }
  }
  
  /**
   * 從佇列中移除題目
   */
  removeQuestion(questionId) {
    const queue = this.loadQueue();
    if (!queue) return;
    
    const newQueue = queue.filter(q => q.id !== questionId);
    this.saveQueue(newQueue);
    console.log('[QueuePersistence] Removed question:', questionId);
  }
  
  /**
   * 獲取佇列統計
   */
  getQueueStats() {
    const queue = this.loadQueue();
    if (!queue) {
      return {
        total: 0,
        ready: 0,
        generating: 0,
        practicing: 0,
        completed: 0
      };
    }
    
    return {
      total: queue.length,
      ready: queue.filter(q => q.status === 'ready').length,
      generating: queue.filter(q => q.status === 'generating').length,
      practicing: queue.filter(q => q.status === 'practicing').length,
      completed: queue.filter(q => q.status === 'completed').length
    };
  }
}

// 創建全域實例
window.queuePersistence = new QueuePersistence();