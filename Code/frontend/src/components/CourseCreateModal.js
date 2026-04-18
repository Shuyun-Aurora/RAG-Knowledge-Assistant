import React, { useContext } from 'react';
import { Modal, Form, Input, message } from 'antd';
import useMessage from "antd/es/message/useMessage";
import UserContext from '../contexts/UserContext';
import {addCourse} from "../service/course";
import {handleBaseApiResponse} from "../utils/message";
import "../css/modal.css"

const CourseCreateModal = ({ open, onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const user = useContext(UserContext);
  const [messageApi, contextHolder] = useMessage();

  const handleCreateCourse = async () => {
    try {
      const values = await form.validateFields(); // 获取表单数据
      const newCourseData = {
        name: values.name,
        description: values.description,
        teacher: user?.username,
      };
      const res = await addCourse(newCourseData);
      await handleBaseApiResponse(res, messageApi, () => {
        onSuccess(res.data); // 传给父组件
        form.resetFields();
        onCancel();
      });
    } catch (error) {
      messageApi.error('请求失败');
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
      <>
      {contextHolder}
    <Modal
      className="neumorphic-modal"
      title="新增开课"
      open={open}
      onCancel={handleCancel}
      onOk={handleCreateCourse}
      okText="创建"
      cancelText="取消"
      afterClose={() => form.resetFields()}
    >
      <Form form={form} layout="vertical">
        <Form.Item 
          label="课程名称" 
          name="name" 
          rules={[{ required: true, message: '请输入课程名称' }]}
        > 
          <Input placeholder="请输入课程名称" />
        </Form.Item>
        <Form.Item 
          label="课程简介" 
          name="description" 
          rules={[{ required: true, message: '请输入课程简介' }]}
        > 
          <Input.TextArea rows={3} placeholder="请输入课程简介" />
        </Form.Item>
        <Form.Item label="授课教师">
          <Input value={user?.username} disabled />
        </Form.Item>
      </Form>
    </Modal>
      </>
  );
};

export default CourseCreateModal; 