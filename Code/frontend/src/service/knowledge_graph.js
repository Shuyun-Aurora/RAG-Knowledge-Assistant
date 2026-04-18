import { getJson, PREFIX, DUMMY_RESPONSE } from './common';

export async function getKnowledgeGraph({ courseName, limit = 100 }) {
    const url = `${PREFIX}/knowledge_graph?course_name=${encodeURIComponent(courseName)}&limit=${limit}`;
    let result;
    try {
        result = await getJson(url);
        console.log(result)
        if (result && result.knowledge_graph && Array.isArray(result.knowledge_graph.nodes)) {
            return result.knowledge_graph;
        }
        return DUMMY_RESPONSE;
    } catch (e) {
        console.error(e);
        return DUMMY_RESPONSE;
    }
}
