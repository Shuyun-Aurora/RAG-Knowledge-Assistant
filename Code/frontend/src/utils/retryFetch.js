import { REQUEST_CONFIG, ERROR_MESSAGES } from '../config/network';

/**
 * 带重试机制的网络请求工具
 * @param {string} url - 请求URL
 * @param {Object} options - fetch选项
 * @param {number} retries - 最大重试次数
 * @param {number} retryDelay - 重试间隔(ms)
 * @returns {Promise} - 请求结果
 */
export const retryFetch = async (
    url, 
    options = {}, 
    retries = REQUEST_CONFIG.MAX_RETRIES, 
    retryDelay = REQUEST_CONFIG.RETRY_DELAY
) => {
    let lastError;
    
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response;
        } catch (error) {
            lastError = error;
            if (i < retries - 1) { // 如果不是最后一次重试
                await new Promise(resolve => setTimeout(resolve, retryDelay));
                // 每次重试增加延迟时间
                retryDelay = retryDelay * REQUEST_CONFIG.RETRY_MULTIPLIER;
            }
        }
    }
    
    throw lastError;
};

/**
 * 检查是否是网络错误
 * @param {Error} error - 错误对象
 * @returns {boolean} - 是否是网络错误
 */
export const isNetworkError = (error) => {
    return (
        error.message === 'Failed to fetch' ||
        error.message === 'Network request failed' ||
        error.message.includes('network') ||
        error instanceof TypeError
    );
};

/**
 * 获取友好的错误消息
 * @param {Error} error - 错误对象
 * @returns {string} - 错误消息
 */
export const getFriendlyErrorMessage = (error) => {
    if (isNetworkError(error)) {
        return ERROR_MESSAGES.NETWORK_ERROR;
    }
    if (error.name === 'TimeoutError') {
        return ERROR_MESSAGES.TIMEOUT_ERROR;
    }
    if (error.message.includes('500')) {
        return ERROR_MESSAGES.SERVER_ERROR;
    }
    return error.message || '请求失败，请稍后重试';
}; 