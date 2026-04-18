import {getJson, PREFIX, put} from "./common";

export async function getMe() {
    const url = `${PREFIX}/user/me`;
    let me = null;
    try {
        me = await getJson(url);
    } catch (e) {
        console.log(e);
    }
    return me;
}

export async function getUserCourseCount() {
    const url = `${PREFIX}/user/course/count`;
    try {
        const response = await getJson(url);
        return {
            success: response.success,
            message: response.message,
            courseCount: response.data
        };
    } catch (e) {
        console.log(e);
        return {
            success: false,
            message: "获取课程数量失败",
            courseCount: 0
        };
    }
}

export async function updateProfile(userData) {
    const url = `${PREFIX}/user/profile`;
    let result;
    try {
        result = await put(url, userData);
    } catch (e) {
        console.log(e);
        result = { success: false, message: "更新失败", data: null };
    }
    return result;
}

export async function changePassword(oldPassword, newPassword) {
    const url = `${PREFIX}/user/password`;
    let result;
    try {
        result = await put(url, { oldPassword, newPassword });
    } catch (e) {
        console.log(e);
        result = { success: false, message: "修改密码失败", data: null };
    }
    return result;
}