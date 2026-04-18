import React from 'react';
import '../css/voice.css'; // 复用原样式

export const SingleChoiceNeumorphic = ({ options, value, onChange, name }) => {
  return (
    <div className="voice-controls">
      {options.map((opt, idx) => (
        <label key={idx} className="voice-toggle-label">
          <input
            type="radio"
            name={name} // 所有 radio 的 name 要一致
            className="voice-toggle-input"
            value={opt}
            checked={value === opt}
            onChange={() => onChange(opt)}
          />
          <span className="icon-box">
            <span className="fa">{opt}</span>
          </span>
        </label>
      ))}
    </div>
  );
};

export const SingleChoiceNeumorphicWithContent = ({ options, value, onChange, name }) => {
    return (
      <div
        className="voice-controls"
        style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'flex-start' }}
      >
        {options.map(({ label, content }, idx) => (
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
              type="radio"
              name={name}
              className="voice-toggle-input"
              value={label}
              checked={value === label}
              onChange={() => onChange(label)}
            />
            <span className="icon-box">
              <span className="fa">{label}</span>
            </span>
            <span style={{ fontSize: '13px', color: '#555' }}>{content}</span>
          </label>
        ))}
      </div>
    );
  };
  