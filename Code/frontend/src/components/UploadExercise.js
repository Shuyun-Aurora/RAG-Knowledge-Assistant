import {useContext, useState, useEffect} from "react";
import {Button, Card, Divider, Input, Select, Space, Typography} from "antd";
import SingleChoiceForm from "./SingleChoiceForm";
import MultiChoiceForm from "./MultiChoiceForm";
import FillInBlankForm from "./FillInBlankForm";
import { PlusOutlined } from '@ant-design/icons';
import useMessage from "antd/es/message/useMessage";
import {uploadExercises} from "../service/exercise";
import {getDocumentsByCourse} from "../service/file";
import CourseContext from "../contexts/CourseContext";

const { Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const UploadExercise = ({ onNewExercise }) => {
  const [type, setType] = useState('single');
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [expanded, setExpanded] = useState(false); // 控制表单展开
  const [questions, setQuestions] = useState([]); 
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [messageApi, contextHolder] = useMessage();
  const { courseId, course } = useContext(CourseContext);
  const courseName = course?.name;

  useEffect(() => {
    console.log("Course info:", { courseId, courseName: course?.name, course });
    console.log("useEffect triggered - expanded:", expanded, "courseName:", courseName);
    if (expanded && courseName) {
      loadDocuments();
    } else if (expanded && !courseName) {
      console.warn("Missing course name:", { course, courseId });
      messageApi.warning('未能获取到课程名称');
    }
  }, [expanded, course]);

  const loadDocuments = async () => {
    if (!courseName) {
      console.warn("Cannot load documents: missing course name");
      return;
    }
    
    try {
      console.log("Fetching documents for course:", courseName);
      const res = await getDocumentsByCourse(courseName);
      console.log("API response:", res);
      
      // 检查返回的数据格式
      if (res.documents && Array.isArray(res.documents)) {
        console.log("Setting documents:", res.documents);
        setDocuments(res.documents);
      } else {
        console.error("Unexpected response format:", res);
        messageApi.error('返回数据格式错误');
      }
    } catch (error) {
      console.error('加载课程资料异常', error);
      messageApi.error(error.message || '加载课程资料出错');
    }
  };

  const handleAddQuestion = (question) => {
    setQuestions([...questions, question]);
    messageApi.success('题目添加成功');
  };

  const handlePublish = async () => {
    if (!title.trim()) return messageApi.warning("请输入习题集标题");
    if (!description.trim()) return messageApi.warning("请输入习题集描述");
    if (questions.length === 0) {
      messageApi.warning('请先添加题目');
      return;
    }
    try {
      console.log({
        course_id: courseId,
        title,
        description,
        questions
      });
      const selectedDocumentObj = documents.find(doc => doc.file_id === selectedDocument);
      const res = await uploadExercises(courseId, {
        title,
        description,
        questions,
        document_id: selectedDocument,
        document_name: selectedDocumentObj ? selectedDocumentObj.filename : null
      });
      if (res.success) {
        messageApi.success('所有题目已提交');
        setQuestions([]);
        setTitle("");
        setDescription("");        
        setSelectedDocument(null);
        setExpanded(false);
        onNewExercise();
      } else {
        messageApi.error(res.message || '提交失败');
      }
    } catch (error) {
      console.error('上传习题异常', error);
      messageApi.error('上传习题出错');
    }
  };

  const typeText = (type) => {
    switch (type) {
      case 'single': return '单选题';
      case 'multiple': return '多选题';
      case 'blank': return '填空题';
      default: return '';
    }
  };

  const handleDelete = (index) => {
    const newQuestions = [...questions];
    newQuestions.splice(index, 1);
    setQuestions(newQuestions);
    messageApi.info(`已删除第 ${index + 1} 题`);
  };

  const renderForm = () => {
    switch (type) {
      case 'single': return <SingleChoiceForm onSubmit={handleAddQuestion} />;
      case 'multiple': return <MultiChoiceForm onSubmit={handleAddQuestion} />;
      case 'blank': return <FillInBlankForm onSubmit={handleAddQuestion} />;
      default: return null;
    }
  };

  return (
      <Card
          className="neumorphic-card"
          title="上传习题"
          extra={
          <>
            {expanded && (
                <Text type="secondary">已添加 {questions.length} 题</Text>
            )}
            <Button 
              className="neumorphic-btn"
              type={expanded ? "default" : "primary"} style={{ marginLeft: 24 }} onClick={() => setExpanded(!expanded)}>
              {expanded ? "取消上传" : "新建习题集"}
            </Button>
          </>
          }
          style={{ marginBottom: 24 }}
      >
        {contextHolder}

        {expanded ? (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Input
              className="neumorphic-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="请输入习题集标题"
          />
          <TextArea
              className="neumorphic-input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请输入习题集描述"
              autoSize={{ minRows: 2, maxRows: 4 }}
          />
          <Select
              className="neumorphic-select"
              value={selectedDocument}
              onChange={setSelectedDocument}
              style={{ width: '100%' }}
              placeholder="选择关联的课程资料（可选）"
              allowClear
          >
            {documents.map(doc => (
              <Option key={doc.file_id} value={doc.file_id}>
                {doc.filename || doc.file_id}
              </Option>
            ))}
          </Select>
          <Select value={type} onChange={setType} style={{ width: 200 }}>
            <Option value="single">单选题</Option>
            <Option value="multiple">多选题</Option>
            <Option value="blank">填空题</Option>
          </Select>
          {renderForm()}
          {questions.length > 0 && (
              <div>
                <Text strong style={{ marginBottom: 20,marginTop: 15, display: 'inline-block' }}>已添加题目：</Text>

<Space direction="vertical" style={{ width: '100%', gap: 16 }}>
  {questions.map((q, index) => (
    <Card
      className="neumorphic-card"
      key={index}
      size="small"
      title={`题目 ${index + 1}（${typeText(q.type)}）`}
      extra={
        <Button
          className="neumorphic-btn"
          danger
          size="small"
          onClick={() => handleDelete(index)}
        >
          删除
        </Button>
      }
    >
      <Paragraph>{q.question}</Paragraph>
      {q.options?.length > 0 && (
        <ul style={{ paddingLeft: 20 }}>
          {q.options.map((opt, i) => (
            <li key={i}>{opt}</li>
          ))}
        </ul>
      )}
      <Paragraph type="secondary">
        答案：{Array.isArray(q.answer) ? q.answer.join(', ') : q.answer}
      </Paragraph>
    </Card>
  ))}
</Space>

              </div>
          )}
          <Divider />
          <Button 
            className="neumorphic-btn"
            type="primary" icon={<PlusOutlined />} onClick={handlePublish}>
            提交所有题目
          </Button>
        </Space>
        ) : (
      <Text type="secondary">点击右上角"新建习题集"以添加习题</Text>)}
      </Card>
  );
};

export default UploadExercise;
