import { retryFetch, isNetworkError, getFriendlyErrorMessage } from '../utils/retryFetch';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';
export const BASEURL = process.env.REACT_APP_BASE_URL || DEFAULT_BASE_URL;
export const PREFIX = `${BASEURL}/api`;

export const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

export async function getJson(url) {
    try {
        let res = await retryFetch(url, {
            method: "GET",
            headers: {
                ...getAuthHeader()
            }
        });
        
        if (!res.ok) {
            return {
                success: false,
                message: `请求失败: ${res.status} ${res.statusText}`,
                data: null
            };
        }
        
        return res.json();
    } catch (error) {
        console.error('请求失败:', error);
        return {
            success: false,
            message: getFriendlyErrorMessage(error),
            data: null
        };
    }
}

export async function get(url) {
    try {
        return await retryFetch(url, {
            method: "GET",
            headers: {
                ...getAuthHeader()
            }
        });
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

export async function post(url, data) {
    try {
        let res = await retryFetch(url, {
            method: "POST",
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
        });
        return res.json();
    } catch (error) {
        console.error('请求失败:', error);
        return {
            success: false,
            message: getFriendlyErrorMessage(error),
            data: null
        };
    }
}

export async function put(url, data) {
    try {
        let res = await retryFetch(url, {
            method: "PUT",
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
        });
        return res.json();
    } catch (error) {
        console.error('请求失败:', error);
        return {
            success: false,
            message: getFriendlyErrorMessage(error),
            data: null
        };
    }
}

export async function postFormData(url, formData) {
    try {
        let res = await retryFetch(url, {
            method: "POST",
            body: formData,
            headers: {
                ...getAuthHeader()
            },
        });
        return res.json();
    } catch (error) {
        console.error('请求失败:', error);
        return {
            success: false,
            message: getFriendlyErrorMessage(error),
            data: null
        };
    }
}

export async function del(url) {
    try {
        let res = await retryFetch(url, {
            method: "DELETE",
            headers: {
                ...getAuthHeader()
            },
        });
        return res.json();
    } catch (error) {
        console.error('请求失败:', error);
        return {
            success: false,
            message: getFriendlyErrorMessage(error),
            data: null
        };
    }
}
export const DUMMY_RESPONSE = {
    success: false,
    message: "网络错误！",
    data: null
}
