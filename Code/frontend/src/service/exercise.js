import {DUMMY_RESPONSE, getJson, post, del, put, PREFIX} from "./common";

export async function uploadExercises(courseId, payload) {
    try {
        const url = `${PREFIX}/exercise/upload`;
        const res = await post(url, {
            course_id: courseId,
            ...payload,
        });
        return res;
    } catch (e) {
        console.error("上传习题出错：", e);
        return DUMMY_RESPONSE;
    }
}

export const fetchExercises = async (courseId, page = 1, pageSize = 10, keyword = '') => {
    const params = new URLSearchParams({
        course_id: courseId,
        page: page.toString(),
        page_size: pageSize.toString(),
    });
    if (keyword) params.append('keyword', keyword);
    const url = `${PREFIX}/exercise/search?${params.toString()}`;
    let res;
    try {
        res = await getJson(url);
    } catch (e) {
        console.log(e);
        res = DUMMY_RESPONSE;
    }
    return res;
};

export async function fetchExerciseSetById(set_id) {
    const url = `${PREFIX}/exercise/${set_id}`;
    try {
        const res = await getJson(url);
        return res;
    } catch (e) {
        console.error(e);
        return DUMMY_RESPONSE;
    }
}


export async function deleteExerciseSet(setId) {
    const url = `${PREFIX}/exercise/${setId}`;
    try {
        const res = await del(url); // 不传第二个参数（即 body）
        return res;
    } catch (e) {
        console.error("删除习题集出错：", e);
        return DUMMY_RESPONSE;
    }
}

export async function updateExercise(exerciseId, payload) {
    try {
        const url = `${PREFIX}/exercise/${exerciseId}`;
        const res = await put(url, payload);
        return res;
    } catch (e) {
        console.error("更新习题出错：", e);
        return DUMMY_RESPONSE;
    }
}