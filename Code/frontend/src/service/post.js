import {DUMMY_RESPONSE, getJson, post, PREFIX} from "./common";

export async function getPost(courseID, skip = 0, limit = 10, keyword = '') {
    const url = `${PREFIX}/course/${courseID}/post?skip=${skip}&limit=${limit}&keyword=${encodeURIComponent(keyword)}`;
    let result;
    try {
        result = await getJson(url);
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

// 发布新帖子
export async function createPost(courseID, { title, content, is_anonymous }) {
    const url = `${PREFIX}/course/${courseID}/post/create`;
    const payload = {
        title,
        content,
        is_anonymous
    };
    let result;
    try {
        result = await post(url, payload);
    } catch (e) {
        console.error(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

export async function getPostById(postId) {
    const url = `${PREFIX}/course/posts/${postId}`;
    let res;
    try {
        res = await getJson(url);
    } catch (e) {
        console.error(e);
        res = DUMMY_RESPONSE;
    }
    return res;
}

export async function getComments(postId, skip = 0, limit = 10) {
    const url = `${PREFIX}/course/posts/${postId}/comments?skip=${skip}&limit=${limit}`;
    let res;
    try {
        res = await getJson(url);
    } catch (e) {
        console.error(e);
        res = DUMMY_RESPONSE;
    }
    return res;
}

export async function addComment(postId, content, parent_id = null, isAnonymous = false) {
    const url = `${PREFIX}/course/posts/${postId}/comments`;
    let res;
    try {
        res = await post(url, { content, parent_id, is_anonymous: isAnonymous });
    } catch (e) {
        console.error(e);
        res = DUMMY_RESPONSE;
    }
    return res;
}