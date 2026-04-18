import {PREFIX, post, DUMMY_RESPONSE} from "./common";

export async function login(username, password) {
    const url = `${PREFIX}/login`;
    let result;
    try {
        result = await post(url, { username, password });
        if (result.success && result.data?.token) {
            localStorage.setItem("token", result.data.token);  // 保存 token
        }
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

export async function register(data) {
    const url = `${PREFIX}/register`;
    let res;
    try {
        res = await post(url, data);
    } catch (e) {
        console.log(e);
        res = DUMMY_RESPONSE;
    }
    return res;
}

export function logout() {
    localStorage.removeItem('token');
    return { success: true, message: 'Logout successful' };
}