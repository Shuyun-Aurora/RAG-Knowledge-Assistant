import { Button, Form, Input } from "antd";
import "../css/neumorphism.css"

const FillInBlankForm = ({ onSubmit }) => {
    const [form] = Form.useForm();

    const handleFinish = (values) => {
        console.log('提交的表单值:', values);
        const { question, answer } = values;
        onSubmit({ type: 'blank', question, answer: answer.split(',') });
        form.resetFields();
    };

    return (
        <div>
            <Form
                form={form}
                layout="vertical"
                onFinish={handleFinish}
                onFinishFailed={(errorInfo) => {
                    console.log('校验失败，错误信息:', errorInfo);
                }}
            >
                <Form.Item
                    name="question"
                    label="题目（可使用下划线表示空格）"
                    rules={[{ required: true, message: "题目不能为空" }]}
                >
                    <Input 
                        className="neumorphic-input"
                        placeholder="如：123是___" 
                    />
                </Form.Item>

                <Form.Item
                    name="answer"
                    label="参考答案（多个答案用英文逗号分隔）"
                    rules={[{ required: true, message: "参考答案不能为空" }]}
                >
                    <Input 
                        className="neumorphic-input"
                        placeholder="如：123,一二三" 
                    />
                </Form.Item>

                <Button 
                    className="neumorphic-btn"
                    htmlType="submit" 
                    type="primary"
                >
                    添加题目
                </Button>
            </Form>
        </div>
    );
};

export default FillInBlankForm;