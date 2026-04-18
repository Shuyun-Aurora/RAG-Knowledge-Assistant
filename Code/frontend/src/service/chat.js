import {PREFIX, getJson, get, post, getAuthHeader} from './common.js';

// Agent风格映射
export const AGENT_STYLES = {
  "默认": "default",
  "严谨导师": "strict_tutor", 
  "热心同学": "friendly_peer",
};

// 获取所有可用的agent风格
// export async function getAgentStyles() {
//   try {
//     const response = await getJson(`${PREFIX}/rag/chat/agent_styles`);
//     return response;
//   } catch (error) {
//     console.error('获取agent风格失败:', error);
//     // 返回默认风格列表
//     return {
//       styles: [
//         { name: "默认", value: "default" },
//         { name: "严谨导师", value: "strict_tutor" },
//         { name: "热心同学", value: "friendly_peer" },
//         { name: "热情导师", value: "enthusiastic_mentor" },
//         { name: "冷静顾问", value: "calm_advisor" }
//       ]
//     };
//   }
// }

// 获取聊天历史
export async function getChatHistory(sessionId) {
  try {
    const response = await getJson(`${PREFIX}/rag/chat_history/${sessionId}`);
    return response;
  } catch (error) {
    console.error('获取聊天历史失败:', error);
    return { session_id: sessionId, history: [] };
  }
}

// 流式聊天请求
export async function streamChat(params, onChunk, onError, onComplete, signal) {;
  const {
    question,
    course_name,
    agent_style = "default",
    filename,
    page_number,
    session_id
  } = params;
  console.log('streamChat params:', params);

  const requestBody = {
    question,
    course_name,
    agent_style,
    filename,
    page_number,
    session_id: session_id || null // 如果是新对话，传null让后端生成
  };

  try {
    const response = await fetch(`${PREFIX}/rag/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify(requestBody),
      signal, // 这里加上 signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        onComplete();
        break;
      }

      // 解码新的chunk并添加到buffer
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // 查找完整的SSE数据行
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.substring(0, newlineIndex);
        buffer = buffer.substring(newlineIndex + 1);
        
        if (line.trim() === '') continue; // 跳过空行
        
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6); // 移除 'data: ' 前缀
            if (jsonStr.trim() === '') continue; // 跳过空数据
            
            const data = JSON.parse(jsonStr);
            
            if (data.type === 'error') {
              onError(data.data);
            } else if (data.type === 'done') {
              // 处理完成信号
              console.log('Stream completed');
            } else {
              // 根据后端格式，数据在data字段中
              if (data.data) {
                console.log('收到数据:', data.data);
                // 传递完整的数据对象，包含类型信息
                onChunk(data);
              }
            }
          } catch (e) {
            console.warn('解析SSE数据失败:', e, '原始数据:', line);
            // 如果不是JSON格式，可能是纯文本数据
            if (line.startsWith('data: ')) {
              const textData = line.slice(6);
              if (textData.trim()) {
                onChunk(textData);
              }
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('流式聊天请求失败:', error);
    onError(error.message);
  }
} 
export const getAgentStyles = async () => {
  try {
    const response = await fetch(`${PREFIX}/rag/chat/agent_styles`, {
      method: 'GET',
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!response.ok) {
      throw new Error('获取Agent风格失败');
    }
    return await response.json();
  } catch (error) {
    console.error('获取Agent风格失败:', error);
    throw error;
  }
};


// 获取聊天历史记录摘要
export async function getChatHistorySummary(courseName = null) {
  try {
    let url = `${PREFIX}/rag/chat_history_summary`;
    if (courseName) {
      url += `?course_name=${encodeURIComponent(courseName)}`;
    }
    console.log('url:', url);
    const response = await getJson(url);
    return response;
  } catch (error) {
    console.error('获取历史记录摘要失败:', error);
    return { summaries: [], total_count: 0 };
  }
}

// 删除聊天会话
export async function deleteChatSession(sessionId) {
  try {
    const response = await fetch(`${PREFIX}/rag/chat_history/${sessionId}`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeader()
      }
    });
    
    if (!response.ok) {
      throw new Error(`删除会话失败: ${response.status}`);
    }
    
    return { success: true };
  } catch (error) {
    console.error('删除会话失败:', error);
    throw error;
  }
};
export const getCurrentReferenceExercises = async (courseName, sessionId) => {
  try {
    const response = await fetch(
      `${PREFIX}/rag/currentReference?course_name=${encodeURIComponent(courseName)}&session_id=${encodeURIComponent(sessionId)}`,
      {
        method: 'GET',
        headers: {
          ...getAuthHeader()
        },
      }
    );
    if (!response.ok) {
      throw new Error('获取习题失败');
    }
    return await response.json();
  } catch (error) {
    console.error('获取习题失败:', error);
    throw error;
  }
}; 