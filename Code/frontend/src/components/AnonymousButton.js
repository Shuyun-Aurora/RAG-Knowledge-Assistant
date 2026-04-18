import React from 'react';
import '../css/voice.css'; // 复用拟态样式

const AnonymousToggle = ({ isAnonymous, onToggle }) => {
  return (
    <div className="voice-controls">
      <label className="voice-toggle-label">
        <input
          type="checkbox"
          className="voice-toggle-input"
          checked={isAnonymous}
          onChange={e => onToggle(e.target.checked)}
        />
        <span className="icon-box">
          <span className="fa">匿名</span>
        </span>
      </label>
    </div>
  );
};

export default AnonymousToggle;
