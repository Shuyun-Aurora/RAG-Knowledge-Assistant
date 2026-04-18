import React from 'react';
import '../css/voice.css'; // 复用原样式

export const MultiChoiceNeumorphic = ({ options, value = [], onChange }) => {
  const handleToggle = (opt) => {
    if (value.includes(opt)) {
      onChange(value.filter((v) => v !== opt)); // 取消选中
    } else {
      onChange([...value, opt]); // 添加选中
    }
  };

  return (
    <div className="voice-controls">
      {options.map((opt, idx) => (
        <label key={idx} className="voice-toggle-label">
          <input
            type="checkbox"
            className="voice-toggle-input"
            value={opt}
            checked={value.includes(opt)}
            onChange={() => handleToggle(opt)}
          />
          <span className="icon-box">
            <span className="fa">{opt}</span>
          </span>
        </label>
      ))}
    </div>
  );
};

export const MultiChoiceNeumorphicWithContent = ({ options, value = [], onChange }) => {
    const handleToggle = (label) => {
      if (value.includes(label)) {
        onChange(value.filter((v) => v !== label));
      } else {
        onChange([...value, label]);
      }
    };
  
    return (
      <div
        className="voice-controls"
        style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'flex-start' }}
      >
        {options.map(({ label, content }, idx) => {
          const checked = value.includes(label);
          return (
            <label
              key={idx}
              className="voice-toggle-label"
              style={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'flex-start',
                gap: '12px',
              }}
            >
              <input
                type="checkbox"
                className="voice-toggle-input"
                value={label}
                checked={checked}
                onChange={() => handleToggle(label)}
              />
              <span className="icon-box">
                <span className="fa">{label}</span>
              </span>
              <span style={{ fontSize: '13px', color: '#555' }}>{content}</span>
            </label>
          );
        })}
      </div>
    );
  };
  