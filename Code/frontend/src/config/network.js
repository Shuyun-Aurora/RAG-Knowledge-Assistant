// API基础URL
export const BASE_URL = process.env.REACT_APP_BASE_URL ?? 'http://127.0.0.1:8000';
export const API_PREFIX = `${BASE_URL}/api`;

// 网络请求配置
export const REQUEST_CONFIG = {
    MAX_RETRIES: 3,           // 最大重试次数
    RETRY_DELAY: 1000,        // 初始重试延迟(ms)
    RETRY_MULTIPLIER: 1.5,    // 重试延迟倍数
    HEALTH_CHECK_INTERVAL: 2000, // 健康检查间隔(ms)
};

// 错误消息
export const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络连接失败，请检查网络后重试',
    SERVER_ERROR: '服务器错误，请稍后重试',
    TIMEOUT_ERROR: '请求超时，请稍后重试',
}; 
