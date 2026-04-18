// API基础URL
export const BASE_URL = process.env.REACT_APP_BASE_URL ?? 'http://127.0.0.1:8000';
export const API_PREFIX = `${BASE_URL}/api`;

// 网络请求配置
export const REQUEST_CONFIG = {
    MAX_RETRIES: 3,           // 最大重试次数
    RETRY_DELAY: 1000,        // 初始重试延迟(ms)
    RETRY_MULTIPLIER: 1.5,    // 重试延迟倍数
    HEALTH_CHECK_INTERVAL: 5000, // 健康检查间隔(ms)
};

// 文件上传配置
export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 1000KB，与后端保持一致
export const UPLOAD_CONFIG = {
    ALLOWED_TYPES: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ],
};

// 错误消息
export const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络连接失败，请检查网络后重试',
    SERVER_ERROR: '服务器错误，请稍后重试',
    TIMEOUT_ERROR: '请求超时，请稍后重试',
    FILE_TOO_LARGE: '文件大小超过限制',
    INVALID_FILE_TYPE: '不支持的文件类型',
};

// 本地存储键名
export const STORAGE_KEYS = {
    TOKEN: 'token',
    USER: 'user',
    THEME: 'theme',
};

// API端点
export const API_ENDPOINTS = {
    LOGIN: '/login',
    REGISTER: '/register',
    USER_INFO: '/user/me',
    HEALTH: '/health',
}; 
