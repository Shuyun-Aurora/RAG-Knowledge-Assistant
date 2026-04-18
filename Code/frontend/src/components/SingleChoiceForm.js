import { Button, Form, Input, Space } from "antd";
import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { useState } from "react";
import { SingleChoiceNeumorphic } from '../components/SingleChoiceButtons';

const SingleChoiceForm = ({ onSubmit }) => {
  const [form] = Form.useForm();
  const [options, setOptions] = useState(["", ""]);
  const [answerIndex, setAnswerIndex] = useState(null); // 用索引管理选择答案

  const handleAddOption = () => {
    setOptions([...options, ""]);
  };

  const handleRemoveOption = (index) => {
    setOptions(options.filter((_, i) => i !== index));
    // 删除后重置答案，如果答案超出范围则清空
    if (answerIndex === index) setAnswerIndex(null);
    else if (answerIndex > index) setAnswerIndex(answerIndex - 1);
  };

  const handleOptionChange = (value, index) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const handleFinish = ({ question }) => {
    if (!question || options.some(opt => !opt) || answerIndex === null) return;
    const answer = String.fromCharCode(65 + answerIndex); // 索引转字母
    onSubmit({ type: "single", question, options, answer });
    form.resetFields();
    setOptions(["", ""]);
    setAnswerIndex(null);
  };

  return (
    <Form form={form} layout="vertical" onFinish={handleFinish}>
      <Form.Item name="question" label="题目" rules={[{ required: true }]}>
        <Input className="neumorphic-input" />
      </Form.Item>

      <Form.Item label="选项">
        {options.map((opt, idx) => (
          <Space key={idx} style={{ display: "flex", marginBottom: 8 }} align="baseline">
            <span style={{ width: 20 }}>{String.fromCharCode(65 + idx)}.</span>
            <Input
              className="neumorphic-input"
              value={opt}
              onChange={(e) => handleOptionChange(e.target.value, idx)}
              style={{ width: 300 }}
            />
            {options.length > 1 && (
              <MinusCircleOutlined onClick={() => handleRemoveOption(idx)} />
            )}
          </Space>
        ))}
        <Button
          className="neumorphic-btn"
          type="dashed"
          onClick={handleAddOption}
          icon={<PlusOutlined />}
          style={{ marginTop: 8 }}
        >
          添加选项
        </Button>
      </Form.Item>

      <Form.Item label="正确答案">
        <SingleChoiceNeumorphic
          options={options.map((_, idx) => String.fromCharCode(65 + idx))}
          value={answerIndex !== null ? String.fromCharCode(65 + answerIndex) : null}
          onChange={(selectedLetter) => {
            if (!selectedLetter) {
              setAnswerIndex(null);
            } else {
              setAnswerIndex(selectedLetter.charCodeAt(0) - 65);
            }
          }}
        />
      </Form.Item>

      <Button className="neumorphic-btn" htmlType="submit" type="primary">
        添加题目
      </Button>
    </Form>
  );
};

export default SingleChoiceForm;
