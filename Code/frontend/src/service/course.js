import {DUMMY_RESPONSE, getJson, post, del, PREFIX} from './common';

// 获取所有课程
export async function getAllCourses({ page = 1, pageSize = 12, keyword = '' } = {}) {
    const url = `${PREFIX}/course/all?page=${page}&pageSize=${pageSize}&keyword=${encodeURIComponent(keyword)}`;
    let res;
    try {
        res = await getJson(url);
    } catch (e) {
        console.log(e);
        res = DUMMY_RESPONSE;
    }
    return res;
}

// 学生加入课程
export async function joinCourse(courseId) {
    const url = `${PREFIX}/course/join/${courseId}`;
    let result;
    try {
        result = await post(url);
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

// 学生退出课程
export async function quitCourse(courseId) {
    const url = `${PREFIX}/course/quit/${courseId}`;
    let result;
    try {
        result = await post(url);
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

// 获取学生加入的课程
export async function getJoinedCourses({ page = 1, pageSize = 12, keyword = '' } = {}) {
    const url = `${PREFIX}/course/join?page=${page}&pageSize=${pageSize}&keyword=${encodeURIComponent(keyword)}`;
    let result;
    try {
        result = await getJson(url);
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

// 获取老师开设的课程
export async function getTaughtCourses({ page = 1, pageSize = 12, keyword = '' } = {}) {
    const url = `${PREFIX}/course/teach?page=${page}&pageSize=${pageSize}&keyword=${encodeURIComponent(keyword)}`;
    let result;
    try {
        result = await getJson(url);
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

export async function getCourseById(courseID) {
    const url = `${PREFIX}/course/${courseID}`;
    let result;
    try {
        result = await getJson(url);
    } catch (e) {
        console.log(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

export async function addCourse(courseData) {
    const url = `${PREFIX}/course/create`;
    let result;
    try {
        result = await post(url, courseData);
    } catch (e) {
        console.error(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}

export async function dissolveCourse(courseId) {
    const url = `${PREFIX}/course/dissolve/${courseId}`;
    let result;
    try {
        result = await post(url);
    } catch (e) {
        console.error(e);
        result = DUMMY_RESPONSE;
    }
    return result;
}