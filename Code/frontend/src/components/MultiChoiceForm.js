import { Button, Form, Input, Space, Checkbox } from "antd";
import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { useState } from "react";
import { MultiChoiceNeumorphic,MultiChoiceNeumorphicWithContent } from "./MultiChoiceButtons";


const MultiChoiceForm = ({ onSubmit }) => {
    const [form] = Form.useForm();
    const [options, setOptions] = useState(["", ""]);
    const [answerIndexes, setAnswerIndexes] = useState([]);

    const handleAddOption = () => {
        setOptions([...options, ""]);
    };

    const handleRemoveOption = (index) => {
        const newOptions = options.filter((_, i) => i !== index);
        setOptions(newOptions);
        setAnswerIndexes(answerIndexes.filter(i => i !== index));
    };

    const handleOptionChange = (value, index) => {
        const newOptions = [...options];
        newOptions[index] = value;
        setOptions(newOptions);
    };

    const handleFinish = ({ question }) => {
        if (!question || options.some(opt => !opt)) return;
        const answer = answerIndexes.map(i => String.fromCharCode(65 + i)); // A, B, ...
        onSubmit({ type: "multiple", question, options, answer });
        form.resetFields();
        setOptions(["", ""]);
        setAnswerIndexes([]);
    };

    return (
        <Form form={form} layout="vertical" onFinish={handleFinish}>
            <Form.Item name="question" label="题目" rules={[{ required: true }]}>
                <Input className="neumorphic-input"/>
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
                <Button className="neumorphic-btn" type="dashed" onClick={handleAddOption} icon={<PlusOutlined />} style={{ marginTop: 8 }}>
                    添加选项
                </Button>
            </Form.Item>

            <Form.Item label="正确答案">
            <MultiChoiceNeumorphic
  options={options.map((_, idx) => String.fromCharCode(65 + idx))} // ['A', 'B', 'C', ...]
  value={answerIndexes.map(idx => String.fromCharCode(65 + idx))} // 将索引转换为字母
  onChange={(selected) => {
    // 将选中的字母转回索引
    const indexes = selected.map(ch => ch.charCodeAt(0) - 65);
    setAnswerIndexes(indexes);
  }}
/>
            </Form.Item>

            <Button className="neumorphic-btn" htmlType="submit" type="primary">
                添加题目
            </Button>
        </Form>
    );
};

export default MultiChoiceForm;
