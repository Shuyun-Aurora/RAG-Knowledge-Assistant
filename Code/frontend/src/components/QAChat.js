import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Avatar, Spin, Typography, Select, Modal, List, message, Card, Tag, Space, Popconfirm } from 'antd';
import { RobotOutlined, UserOutlined, SendOutlined, BookOutlined, CopyOutlined, CheckOutlined, DownOutlined, UpOutlined, StopOutlined, HistoryOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { streamChat, getAgentStyles, getChatHistory, getChatHistorySummary, deleteChatSession, getCurrentReferenceExercises } from '../service/chat.js';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ExerciseCard from './ExerciseCard';
import { AudioOutlined, SoundOutlined } from '@ant-design/icons';
import { Switch, Radio } from 'antd';
import VoiceControls from './VoiceControls';

const { Text } = Typography;
const { Option } = Select;

const CustomPre = ({ children }) => {
  const [copied, setCopied] = useState(false);
  let textToCopy = '';

  if (children && React.Children.count(children) > 0) {
    const codeElement = React.Children.toArray(children)[0];
    if (codeElement.props && codeElement.props.children) {
      textToCopy = String(codeElement.props.children).replace(/\n$/, '');
    }
  }

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const handleCopy = async () => {
    if (!textToCopy) {
      message.error('没有可复制的内容。');
      return;
    }
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      message.success('已复制到剪贴板！');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      message.error('复制失败，请手动复制。');
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <Button
        size="small"
        type="text"
        icon={copied ? <CheckOutlined /> : <CopyOutlined />}
        onClick={handleCopy}
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          zIndex: 1,
          color: copied ? '#52c41a' : '#8c8c8c',
          background: 'rgba(240, 242, 245, 0.7)',
          border: '1px solid #d9d9d9',
          backdropFilter: 'blur(2px)'
        }}
      />
      <pre>{children}</pre>
    </div>
  );
};

const SourceDisplay = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{
      marginTop: '16px',
      padding: '12px',
      backgroundColor: '#f8f9fa',
      borderRadius: '6px',
      border: '1px solid #e9ecef',
      maxWidth: '100%',
      overflowX: 'auto'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '8px'
      }}>
        <div style={{
          fontSize: '14px',
          fontWeight: 'bold',
          color: '#495057'
        }}>
          📚 参考来源 ({sources.length})
        </div>
        <Button
          type="text"
          size="small"
          icon={expanded ? <UpOutlined /> : <DownOutlined />}
          onClick={() => setExpanded(!expanded)}
          style={{
            color: '#1677ff',
            fontSize: '12px'
          }}
        >
          {expanded ? '收起' : '展开'}
        </Button>
      </div>

      {expanded && (
        <div>
          {sources.map((source, index) => (
            <div key={`source-exp-${index}`} style={{
              marginBottom: '12px',
              padding: '8px',
              backgroundColor: 'white',
              borderRadius: '4px',
              border: '1px solid #dee2e6',
              maxWidth: '100%',
              overflowX: 'auto'
            }}>
              <div style={{ 
                fontSize: '12px', 
                color: '#6c757d', 
                marginBottom: '8px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span>来源 {index + 1}</span>
                {source.metadata?.filename && (
                  <span style={{ 
                    fontSize: '11px', 
                    color: '#1677ff',
                    backgroundColor: '#f0f8ff',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    border: '1px solid #d6e4ff'
                  }}>
                    📄 {source.metadata.filename}
                  </span>
                )}
              </div>
              <div className="markdown-content" style={{ fontSize: '13px', lineHeight: '1.5', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxWidth: '100%', overflowX: 'auto' }}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    pre: CustomPre,
                    img: (props) => (
                      <img {...props} style={{ maxWidth: '100%' }} alt="" />
                    )
                  }}
                >
                  {source.page_content}
                </ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const QAChat = ({
  initialHistory = [],
  courseName = "离散数学",
  filename = null,
  pageNumber = null,
  sessionId = null,
  referenceBar = null // 添加默认值为null的referenceBar属性
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState(initialHistory);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agentStyle, setAgentStyle] = useState('default');
  const [agentStyles, setAgentStyles] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);
  const [showModal, setShowModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historySummaries, setHistorySummaries] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);
  const messageListRef = useRef(null);
  const [exercises, setExercises] = useState([]);
  const [loadingExercises, setLoadingExercises] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [exerciseResults, setExerciseResults] = useState({});
  const aiMessageIndexRef = useRef(null);
  const lastReadAnswerIndexRef = useRef(-1);

  const [inputMode, setInputMode] = useState('text'); // 'text' or 'voice'
  const [speechEnabled, setSpeechEnabled] = useState(false); // 语音播报开关
  const recognitionRef = useRef(null); // 语音识别实例
  const [listening, setListening] = useState(false); // 是否正在语音识别

  const options = [
    { label: "文字输入", val: "text" },
    { label: "语音输入", val: "voice" },
  ];


  // 语音识别回调，识别完成后直接填入 inputValue 并切换回文本输入
  const startVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      message.error('当前浏览器不支持语音识别');
      return;
    }
    if (!recognitionRef.current) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.lang = 'zh-CN';
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setListening(false);
        setInputMode('text'); // 识别完成后切回文本输入
      };
      recognitionRef.current.onerror = (event) => {
        message.error('语音识别失败: ' + event.error);
        setListening(false);
        setInputMode('text');
      };
      recognitionRef.current.onend = () => {
        setListening(false);
        setInputMode('text');
      };
    }
    setListening(true);
    recognitionRef.current.start();
  };
  
  const stopVoiceInput = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setListening(false);
      setInputMode('text'); // 停止后回到文字输入
    }
  };

  // 合并语音播报朗读逻辑，只保留一个useEffect
  useEffect(() => {
    if (!speechEnabled) return;
    if (isLoading) return;
    if (messages.length === 0) return;
    // 找到最后一条AI回复
    for (let i = messages.length - 1; i >= 0; i--) {
      const lastMsg = messages[i];
      if (lastMsg.type === 'answer' && lastMsg.content) {
        if (lastReadAnswerIndexRef.current !== i) {
          lastReadAnswerIndexRef.current = i;
          const utter = new window.SpeechSynthesisUtterance(lastMsg.content);
          utter.lang = 'zh-CN';
          window.speechSynthesis.speak(utter);
        }
        break;
      }
    }
  }, [isLoading, messages, speechEnabled]);

  // 新增：监听speechEnabled关闭时停止语音播报
  useEffect(() => {
    if (!speechEnabled) {
      window.speechSynthesis.cancel();
    }
  }, [speechEnabled]);


  const agentStyleNames = {
    "default": "默认",
    "strict_tutor": "严谨导师",
    "friendly_peer": "热心同学"
  };

  const scrollToBottom = () => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  };

  useEffect(scrollToBottom, [messages]);

  const convertToBeijingTime = (utcTimeString) => {
    if (!utcTimeString) return new Date().toISOString();
    try {
      const utcDate = new Date(utcTimeString);
      const beijingDate = new Date(utcDate.getTime() + 8 * 60 * 60 * 1000);
      return beijingDate.toISOString();
    } catch (error) {
      console.error('时间转换失败:', error);
      return new Date().toISOString();
    }
  };

  const formatHistoryData = (historyData) => {
    if (!historyData || !Array.isArray(historyData)) return [];
    return historyData.map(item => {
      const isUser = item.type === 'human';
      const formattedMessage = {
        type: isUser ? 'question' : 'answer',
        content: item.data?.content || '',
        user: isUser ? '我' : 'AI 助教',
        timestamp: convertToBeijingTime(item.data?.timestamp)
      };
      
      if (!isUser && item.data?.additional_kwargs?.sources) {
        formattedMessage.sources = item.data.additional_kwargs.sources;
      }
      
      return formattedMessage;
    });
  };

  const loadHistorySummary = async () => {
    setLoadingHistory(true);
    try {
      // 只传 courseName
      const data = await getChatHistorySummary(courseName);
      setHistorySummaries(data.summaries || []);
    } catch (error) {
      message.error('加载历史记录失败');
      console.error('加载历史记录失败:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const continueChat = async (sessionId) => {
    setShowHistoryModal(false);
    try {
      const result = await getChatHistory(sessionId);
      if (result.history && result.history.length > 0) {
        const formattedHistory = formatHistoryData(result.history);
        setMessages(formattedHistory);
        setCurrentSessionId(sessionId);
      } else {
        setMessages([]);
        setCurrentSessionId(sessionId);
      }
      navigate(`?session_id=${sessionId}`, { replace: true });
    } catch (error) {
      message.error('加载历史记录失败');
      console.error('加载历史记录失败:', error);
      setCurrentSessionId(sessionId);
      setMessages([]);
      navigate(`?session_id=${sessionId}`, { replace: true });
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteChatSession(sessionId);
      message.success('删除成功');
      loadHistorySummary();
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
    } catch (error) {
      message.error('删除失败');
    }
  };
  const handleNewChat = () => {
    // 清空当前会话状态，和刷新页面效果相同
    setCurrentSessionId(null);
    setMessages([]);
    setSelectedAnswers({});
    setExerciseResults({});
    setExercises([]);
    
    // 清除URL中的session_id参数
    navigate('', { replace: true });
    
    // 关闭历史记录模态框（如果打开的话）
    setShowHistoryModal(false);
    
    message.success('已开始新对话');
  };

  useEffect(() => {
    const loadAgentStyles = async () => {
      const fallbackStyles = Object.entries(agentStyleNames).map(([value, name]) => ({ value, name }));
      try {
        const result = await getAgentStyles();
        if (result && Array.isArray(result.styles)) {
          const fetchedStyles = result.styles
            .filter(apiStyle => apiStyle && apiStyle.style && apiStyle.name)
            .map(apiStyle => ({
              value: apiStyle.style,
              name: apiStyle.name,
            }));
          setAgentStyles(fetchedStyles);
        } else {
          console.error('API未返回有效styles数组，使用备用列表。');
          setAgentStyles(fallbackStyles);
        }
      } catch (error) {
        console.error('加载agent风格失败，使用备用列表:', error);
        setAgentStyles(fallbackStyles);
      }
    };
    loadAgentStyles();
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      const loadChatHistory = async () => {
        try {
          const result = await getChatHistory(currentSessionId);
          if (result.history && result.history.length > 0) {
            const formattedHistory = formatHistoryData(result.history);
            setMessages(formattedHistory);
          }
        } catch (error) {
          console.error('加载聊天历史失败:', error);
        }
      };
      loadChatHistory();
    }
  }, [currentSessionId]);

  useEffect(() => {
    if (sessionId && sessionId !== currentSessionId) {
      continueChat(sessionId);
    }
  }, [sessionId]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      type: 'question',
      content: inputValue,
      user: '我',
      timestamp: convertToBeijingTime(new Date().toISOString())
    };

    const aiMessage = {
      type: 'answer',
      content: '',
      user: 'AI 助教',
      timestamp: convertToBeijingTime(new Date().toISOString())
    };

    setMessages(prev => {
      const newMessages = [...prev, userMessage, aiMessage];
      aiMessageIndexRef.current = newMessages.length - 1;
      return newMessages;
    });

    setInputValue('');
    setIsLoading(true);

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      await streamChat(
        {
          question: inputValue,
          course_name: courseName,
          agent_style: agentStyle,
          filename: filename,
          page_number: pageNumber,
          session_id: currentSessionId
        },
        (chunk) => {
          setMessages(prev => {
            const index = aiMessageIndexRef.current;
            if (index === null || index >= prev.length) return prev;

            const currentAI = prev[index];
            let contentToAdd = '';
            let sourcesToAdd = null;
            let sessionIdFromBackend = null;

            if (typeof chunk === 'string') {
              contentToAdd = chunk;
            } else if (chunk && typeof chunk === 'object') {
              if (chunk.type === 'source') {
                sourcesToAdd = chunk.data || [];
              } else if (chunk.type === 'content' && chunk.session_id) {
                contentToAdd = chunk.data || '';
                sessionIdFromBackend = chunk.session_id;
              } else if (chunk.data) {
                contentToAdd = chunk.data;
              }
            }

            if (sessionIdFromBackend && !currentSessionId) {
              setCurrentSessionId(sessionIdFromBackend);
            }

            const updatedMessage = {
              ...currentAI,
              content: currentAI.content + contentToAdd
            };

            if (sourcesToAdd) {
              updatedMessage.sources = sourcesToAdd;
            }

            const newMessages = [...prev];
            newMessages[index] = updatedMessage;
            return newMessages;
          });
        },
        (error) => {
          if (error.name !== 'AbortError') {
            message.error(`聊天请求失败: ${error.message}`);
          }
          setIsLoading(false);
        },
        () => {
          setIsLoading(false);
          abortControllerRef.current = null;
        },
        abortControllerRef.current.signal
      );
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('发送消息失败:', error);
        message.error('发送消息失败，请重试');
      }
      setIsLoading(false);
    }
  };

  const fetchExercises = async () => {
    if (!currentSessionId || !courseName) {
      message.error('无法获取习题：缺少必要参数');
      return;
    }

    setLoadingExercises(true);
    try {
      const response = await getCurrentReferenceExercises(courseName, currentSessionId);
      const allExercises = [];
      
      response.references.forEach(ref => {
        if (ref.exercises && ref.exercises.length > 0) {
          ref.exercises.forEach(exercise => {
            allExercises.push({
              ...exercise,
              documentName: ref.filename
            });
          });
        }
      });
      
      setExercises(allExercises);
      const initialAnswers = {};
      allExercises.forEach(exercise => {
        initialAnswers[exercise.id] = '';
      });
      setSelectedAnswers(initialAnswers);
      setExerciseResults({});
      
      if (allExercises.length === 0) {
        message.info('当前对话没有相关的习题');
      }
    } catch (error) {
      message.error('获取习题失败：' + error.message);
    } finally {
      setLoadingExercises(false);
    }
  };

  const handleAnswerSelect = (exerciseId, value) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [exerciseId]: value
    }));
  };

  const checkAnswer = (exercise) => {
    const selectedAnswer = selectedAnswers[exercise.id];
    if (!selectedAnswer) {
      message.warning('请先选择答案');
      return;
    }

    let isCorrect = false;
    if (exercise.type === 'single') {
      const index = exercise.options.indexOf(selectedAnswer);
      const selectedLetter = String.fromCharCode(65 + index);
      isCorrect = selectedLetter === exercise.answer;
    } 
    else if (exercise.type === 'multiple') {
      const selectedLetters = selectedAnswer.map(answer => {
        const index = exercise.options.indexOf(answer);
        return String.fromCharCode(65 + index);
      }).sort();

      const correctAnswers = Array.isArray(exercise.answer) ? exercise.answer : [exercise.answer];
      isCorrect = JSON.stringify(selectedLetters) === JSON.stringify(correctAnswers.sort());
    } 
    else if (exercise.type === 'blank') {
      const userAnswers = selectedAnswer.split(',').map(ans => ans.trim());
      const correctAnswers = Array.isArray(exercise.answer) ? exercise.answer : [exercise.answer];
      
      isCorrect = userAnswers.some(ans => 
        correctAnswers.some(correct => 
          correct.toLowerCase() === ans.toLowerCase()
        )
      );
    }

    setExerciseResults(prev => ({
      ...prev,
      [exercise.id]: isCorrect
    }));
  };

  const renderExercise = (exercise) => {
    const result = exerciseResults[exercise.id];
    return (
      <ExerciseCard
        key={exercise.id}
        exercise={exercise}
        selectedAnswer={selectedAnswers[exercise.id]}
        onAnswerSelect={handleAnswerSelect}
        onSubmit={checkAnswer}
        result={result}
      />
    );
  };

  const handleExerciseButtonClick = async () => {
    setShowModal(true);
    await fetchExercises();
  };

  const truncate = (str, n) => (str && str.length > n ? str.slice(0, n) + '...' : str);

    return (
      <div className="qa-container" style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: 'calc(100vh - 200px)',
        position: 'relative',
        margin: '-24px',
        padding: '0',
        overflow: 'hidden' // Add this to prevent background showing through
      }}>
        {/* 选择引用和页码选择栏由父组件传入 referenceBar，直接渲染在输入区下方 */}
        <div
          className="qa-message-list"
          ref={messageListRef}
          style={{
            flex: 1,
            padding: '24px',
            backgroundColor: 'transparent', // Make less transparent
            overflowY: 'auto', // Always show scrollbar when needed
            display: 'flex',
            flexDirection: 'column',
            justifyContent: messages.length === 0 ? 'center' : 'flex-start',
            minHeight: 0 // Important for flex children to respect overflow
          }}
        >
        {messages.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            fontSize: '16px',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            <RobotOutlined style={{ fontSize: '64px', marginBottom: '24px', display: 'block' }} />
            <div style={{ fontSize: '18px', fontWeight: 500, marginBottom: '8px' }}>开始与AI助教对话吧！</div>
            <div style={{ fontSize: '14px' }}>你可以询问任何关于课程的问题</div>
          </div>
        )}
        {messages.map((msg, index) => (
          <div 
            key={`${msg.type}-${index}-${msg.timestamp}`} 
            style={{
              display: 'flex',
              justifyContent: msg.type === 'question' ? 'flex-end' : 'flex-start',
              marginBottom: '16px',
              width: '100%'
            }}
          >
            <div 
              style={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'flex-start',
                maxWidth: '80%'
              }}
            >
              {msg.type === 'answer' && (
                <>
                  <Avatar icon={<RobotOutlined />} style={{ marginRight: '12px', flexShrink: 0 }} />
                  <div className="qa-message-content" style={{
                    padding: '12px 16px',
                    borderRadius: '18px 18px 18px 0',
                    backgroundColor: 'rgba(207, 212, 215, 0.6)',
                    color: '#333',
                    wordBreak: 'break-word'
                  }}>
                    <div className="markdown-content">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                        components={{
                          pre: CustomPre
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                      {msg.sources && msg.sources.length > 0 && (
                        <SourceDisplay sources={msg.sources} />
                      )}
                    </div>
                  </div>
                </>
              )}
              {msg.type === 'question' && (
                <>
                  <div className="qa-message-content" style={{ backgroundColor: "rgba(135, 169, 193, 0.6)", color: '#333', wordBreak: 'break-word', whiteSpace: 'pre-wrap', marginRight: '12px', borderRadius: '18px 18px 0 18px', padding: '12px 16px' }}>
                    {msg.content}
                  </div>
                  <Avatar icon={<UserOutlined />} style={{ flexShrink: 0 }} />
                </>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-start',
            marginBottom: '16px',
            width: '100%'
          }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Avatar icon={<RobotOutlined />} style={{ marginRight: '12px' }} />
              <div style={{ 
                padding: '12px 16px',
                borderRadius: '18px 18px 18px 0',
                backgroundColor: '#f0f0f0'
              }}>
                <Spin size="small" />
                <Text style={{ marginLeft: 8, color: '#333' }}>AI 助教正在思考...</Text>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="qa-input-area" style={{ 
        padding: '16px 24px', 
        borderTop: '1px solid #e8e8e8',
        backgroundColor: 'rgba(255, 255, 255, 0.33)',
        flexShrink: 0,
        boxShadow: '0 -2px 8px rgba(0,0,0,0.06)'
      }}>
  {/* 选择引用和页码选择栏 */}
  {referenceBar}

  {/* Voice controls section */}

        <div style={{ display: 'flex', gap: 12, marginBottom: 12, alignItems: 'center' }}>
          {inputMode === 'text' ? (
            <Input
              className="neumorphic-input"
              style={{ flex: 1, borderRadius: '8px', fontSize: '14px', resize: 'none' }}
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onPressEnter={e => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="在此输入你的问题...(Enter发送，Shift+Enter换行)"
              disabled={isLoading}
              size="large"
              autoSize={{ minRows: 1, maxRows: 6 }}
            />
          ) : (
            <Button
              className="neumorphic-btn"
              type={listening ? "primary" : "default"}
              icon={<AudioOutlined />}
              onClick={listening ? stopVoiceInput : startVoiceInput}
              loading={listening}
              size="large"
              style={{ flex: 1, height: 40, borderRadius: 8, fontWeight: 500 }}
            >
              {listening ? "正在聆听...点击停止" : "点击开始语音输入"}
            </Button>
          )}
          <VoiceControls
            inputMode={inputMode}
            speechEnabled={speechEnabled}
            onVoiceInputChange={active => setInputMode(active ? 'voice' : 'text')}
            onVoiceOutputChange={setSpeechEnabled}
          />
          <Button
            className="neumorphic-btn"
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isLoading}
            size="large"
            style={{ width: 100, borderRadius: '8px', fontWeight: 500 }}
            disabled={inputMode === 'voice' && (!inputValue || listening)}
          >
            发送
          </Button>
          
          {isLoading && (
            <Button
              className="neumorphic-btn"
              icon={<StopOutlined />}
              type="default"
              danger
              size="large"
              onClick={() => {
                if (abortControllerRef.current) {
                  abortControllerRef.current.abort();
                  abortControllerRef.current = null;
                }
                setIsLoading(false);
              }}
              style={{
                width: 100,
                borderRadius: '8px',
                fontWeight: 500,
                marginLeft: 8
              }}
            >
              停止
            </Button>
          )}
        </div>

        <div style={{ 
          display: 'flex', 
          alignItems: 'center',
          gap: 16, 
          justifyContent: 'space-between' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Select
              value={agentStyle}
              onChange={value => setAgentStyle(value)}
              style={{ width: 140, height: 40, display: 'flex', alignItems: 'center' }}
              size="middle"
            >
              {agentStyles.map(style => (
                <Option key={style.value} value={style.value}>
                  {style.name}
                </Option>
              ))}
            </Select>
          </div>
          
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              className="neumorphic-btn"
              icon={<BookOutlined />}
              type="default"
              size="middle"
              onClick={handleExerciseButtonClick}
              style={{
                borderColor: '#dbeafe',
                backgroundColor: '#eff6ff',
                color: '#2563eb',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                borderRadius: '6px'
              }}
            >
              推送习题
            </Button>
            <Button
              className="neumorphic-btn"
              icon={<HistoryOutlined />}
              type="default"
              size="middle"
              onClick={() => {
                setShowHistoryModal(true);
                loadHistorySummary();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                borderRadius: '6px'
              }}
            >
              历史记录
            </Button>
            <Button
              className="neumorphic-btn"
              icon={<PlusOutlined />}
              type="primary"
              size="middle"
              onClick={handleNewChat}
              style={{
                display: 'flex',
                alignItems: 'center',
                borderRadius: '6px'
              }}
            >
              新建对话
            </Button>
          </div>
        </div>
      </div>

      <Modal
        className="neumorphic-modal"
        open={showModal}
        title="相关习题"
        onCancel={() => setShowModal(false)}
        footer={null}
        width={800}
      >
        {loadingExercises ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px', color: '#666' }}>正在加载习题...</div>
          </div>
        ) : exercises.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            当前对话没有相关的习题
          </div>
        ) : (
          <List
            dataSource={exercises}
            renderItem={exercise => (
              <List.Item>
                <ExerciseCard
                  exercise={exercise}
                  selectedAnswer={selectedAnswers[exercise.id]}
                  onAnswerSelect={handleAnswerSelect}
                  onSubmit={checkAnswer}
                  result={exerciseResults[exercise.id]}
                  style={{ width: '100%', marginBottom: 0 }}
                />
              </List.Item>
            )}
          />
        )}
      </Modal>
      
      <Modal
        className="neumorphic-modal"
        open={showHistoryModal}
        title="聊天历史记录"
        onCancel={() => setShowHistoryModal(false)}
        footer={null}
        width={800}
      >
        {loadingHistory ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px', color: '#666' }}>加载历史记录中...</div>
          </div>
        ) : historySummaries.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            暂无历史记录
          </div>
        ) : (
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {historySummaries.map((summary, index) => (
              <Card
                key={summary.session_id}
                style={{ marginBottom: '16px', border: '1px solid #f0f0f0' }}
                bodyStyle={{ padding: '16px' }}
                className="history-item"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontSize: '16px',
                        fontWeight: 'bold',
                        color: '#333',
                        marginBottom: '8px'
                      }}
                    >
                      {truncate(summary.first_question, 40)}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                      <Space>
                        <span>消息数: {summary.message_count}</span>
                        <span>创建时间: {new Date(convertToBeijingTime(summary.created_at)).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}</span>
                        <span>更新时间: {new Date(convertToBeijingTime(summary.updated_at)).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}</span>
                      </Space>
                    </div>
                  </div>
                  <Tag color="blue" style={{ marginLeft: '8px' }}>
                    {summary.message_count} 条消息
                  </Tag>
                </div>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  <Button
                    type="primary"
                    size="small"
                    icon={<HistoryOutlined />}
                    onClick={() => continueChat(summary.session_id)}
                  >
                    继续对话
                  </Button>
                  <Popconfirm
                    title="确定要删除这个会话吗？"
                    onConfirm={() => handleDeleteSession(summary.session_id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      className='neumorphic-btn'
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      danger
                    >
                      删除
                    </Button>
                  </Popconfirm>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default QAChat;