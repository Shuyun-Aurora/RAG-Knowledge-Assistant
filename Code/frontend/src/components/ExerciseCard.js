import React from 'react';
import { Card, Tag, Radio, Checkbox, Input, Button, Space } from 'antd';
import { SingleChoiceNeumorphicWithContent } from './SingleChoiceButtons';
import { MultiChoiceNeumorphicWithContent } from './MultiChoiceButtons';

const ExerciseCard = ({ 
  exercise, 
  selectedAnswer, 
  onAnswerSelect, 
  onSubmit, 
  result,
  style 
}) => {
  return (
    <Card 
      className='neumorphic-card'
      style={{ 
        marginBottom: 16,
        border: result !== undefined 
          ? (result ? '1px solid #52c41a' : '1px solid #ff4d4f')
          : '1px solid #d9d9d9',
        ...style
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <Tag color="blue">{exercise.documentName}</Tag>
        <Tag color={
          exercise.type === 'single' ? 'green' 
          : exercise.type === 'multiple' ? 'orange'
          : 'purple'
        }>
          {exercise.type === 'single' ? '单选题'
          : exercise.type === 'multiple' ? '多选题'
          : '填空题'}
        </Tag>
      </div>
      
      <div style={{ marginBottom: 16 }}>
        <strong>{exercise.question}</strong>
      </div>

      {exercise.type === 'single' && (
        <SingleChoiceNeumorphicWithContent
          options={exercise.options.map((opt, idx) => ({ label: String.fromCharCode(65 + idx), content: opt }))}
          value={selectedAnswer ? String.fromCharCode(65 + exercise.options.indexOf(selectedAnswer)) : null}
          onChange={(selectedLetter) => {
            if (!selectedLetter) {
              onAnswerSelect(exercise.id, null);
            } else {
              const idx = selectedLetter.charCodeAt(0) - 65;
              onAnswerSelect(exercise.id, exercise.options[idx]);
            }
          }}
          style={{ marginBottom: 16 }}
        />
      )}

      {exercise.type === 'multiple' && (
        <MultiChoiceNeumorphicWithContent
          options={exercise.options.map((opt, idx) => ({ label: String.fromCharCode(65 + idx), content: opt }))}
          value={Array.isArray(selectedAnswer) ? selectedAnswer.map(opt => String.fromCharCode(65 + exercise.options.indexOf(opt))) : []}
          onChange={(selectedLetters) => {
            if (!selectedLetters || selectedLetters.length === 0) {
              onAnswerSelect(exercise.id, []);
            } else {
              const opts = selectedLetters.map(letter => exercise.options[letter.charCodeAt(0) - 65]);
              onAnswerSelect(exercise.id, opts);
            }
          }}
          style={{ marginBottom: 16 }}
        />
      )}

      {exercise.type === 'blank' && (
        <Input
          value={selectedAnswer || ''}
          onChange={(e) => onAnswerSelect(exercise.id, e.target.value)}
          placeholder="请输入答案，多个答案请用英文逗号分隔"
          style={{ marginBottom: 16 }}
        />
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 20 }}>
        <Button 
          type="primary"
          onClick={() => onSubmit(exercise)}
        >
          提交答案
        </Button>
        
        {result !== undefined && (
          <Tag color={result ? 'success' : 'error'}>
            {result ? '答案正确' : '答案错误'}
          </Tag>
        )}
      </div>
    </Card>
  );
};

export default ExerciseCard; 