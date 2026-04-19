import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Typography, Space, Tag, Input, Button, message } from 'antd';
import { fetchExerciseSetById } from "../service/exercise";
import {SingleChoiceNeumorphicWithContent} from '../components/SingleChoiceButtons'; // 你也可以分开从不同文件导入
import { MultiChoiceNeumorphicWithContent } from '../components/MultiChoiceButtons';

const { Title, Paragraph, Text } = Typography;

const ExerciseDetailPage = () => {
  const { exerciseId } = useParams();
  const [exerciseSet, setExerciseSet] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!exerciseId) return;
    fetchExerciseSetById(exerciseId).then(res => {
      if (res.success) {
        setExerciseSet(res.data);
      } else {
        message.error(res.message || "获取习题集失败");
      }
    }).catch(() => {
      message.error("请求失败");
    });
  }, [exerciseId]);

  const getTypeLabel = (type) => {
    switch (type) {
      case 'single': return '单选题';
      case 'multiple': return '多选题';
      case 'blank': return '填空题';
      default: return type;
    }
  };

  const handleChange = (id, value) => {
    setUserAnswers(prev => ({ ...prev, [id]: value }));
  };

  const handleSubmit = () => {
    if (!exerciseSet?.exercises.length) return;
    setSubmitted(true);
  };

  const handleReset = () => {
    setUserAnswers({});
    setSubmitted(false);
  };

  const renderFeedback = (exercise) => {
    const userAnswer = userAnswers[exercise.id];
    const correctAnswer = JSON.parse(exercise.answer);

    let normalizedUserAnswer;
    if (exercise.type === 'single') {
      normalizedUserAnswer = userAnswer || '';
    } else if (exercise.type === 'multiple') {
      normalizedUserAnswer = [...(userAnswer || [])].sort();
    } else if (exercise.type === 'blank') {
      normalizedUserAnswer = (userAnswer || '').split(',').map(s => s.trim());
      const isCorrect = normalizedUserAnswer.some(ans => correctAnswer.includes(ans));
      return (
        <div style={{ marginTop: 8 }}>
          {isCorrect ? <Tag color="green">✅ 正确</Tag> : <Tag color="red">❌ 错误</Tag>}
        </div>
      );
    }

    const isCorrect = JSON.stringify(normalizedUserAnswer) === JSON.stringify(correctAnswer);
    return (
      <div style={{ marginTop: 8 }}>
        {isCorrect ? <Tag color="green">✅ 正确</Tag> : <Tag color="red">❌ 错误</Tag>}
      </div>
    );
  };

  if (!exerciseSet) return <div>没有找到习题集</div>;

  return (
    <Card className='neumorphic-card' style={{ padding: 20 }}>
      <Title level={3}>{exerciseSet.title}</Title>
      <Paragraph>{exerciseSet.description}</Paragraph>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {exerciseSet.exercises.map((exercise, index) => {
          const options = JSON.parse(exercise.options || '[]');

          // 生成带label和content的options格式 [{label:'A', content:'选项内容'}, ...]
          const formattedOptions = options.map((content, idx) => ({
            label: String.fromCharCode(65 + idx),
            content,
          }));

          const userAnswer = userAnswers[exercise.id];

          return (
            <Card 
              className='neumorphic-card' 
              key={exercise.id} 
              size="small" 
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span>{`第 ${index + 1} 题`}</span>
                <Tag color="blue">{getTypeLabel(exercise.type)}</Tag>
              </div>
              }
            >
              <Text strong style={{ display: 'block', marginTop: 4, marginBottom: 16 }}>{exercise.question}</Text>
              <div style={{ marginTop: 20 }}>
                {exercise.type === 'single' && (
                  <SingleChoiceNeumorphicWithContent
                    options={formattedOptions}
                    value={userAnswer}
                    onChange={val => handleChange(exercise.id, val)}
                    name={`exercise-${exercise.id}`}
                  />
                )}
                {exercise.type === 'multiple' && (
                  <MultiChoiceNeumorphicWithContent
                    options={formattedOptions}
                    value={userAnswer || []}
                    onChange={vals => handleChange(exercise.id, vals)}
                  />
                )}
                {exercise.type === 'blank' && (
                  <Input
                    className='neumorphic-input'
                    placeholder="请输入你的答案"
                    value={userAnswer || ''}
                    onChange={e => handleChange(exercise.id, e.target.value)}
                  />
                )}
              </div>

              {submitted && renderFeedback(exercise)}
            </Card>
          );
        })}

        {submitted ? (
          <Button className='neumorphic-btn' type="primary" ghost onClick={handleReset}>
            重新作答
          </Button>
        ) : (
          <Button className='neumorphic-btn' type="primary" onClick={handleSubmit}>
            提交答案
          </Button>
        )}
      </Space>
    </Card>
  );
};

export default ExerciseDetailPage;
