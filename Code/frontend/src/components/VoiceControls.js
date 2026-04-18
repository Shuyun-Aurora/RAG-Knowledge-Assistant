import React from 'react';
import '../css/voice.css'; // 我们后面写样式

const VoiceControls = ({ inputMode, speechEnabled, onVoiceInputChange, onVoiceOutputChange }) => {
  // 受控组件，交互由input[type=checkbox]控制
  return (
    <div className="voice-controls">
      {/* 语音输入按钮 */}
      <label className="voice-toggle-label">
        <input
          type="checkbox"
          className="voice-toggle-input"
          checked={inputMode === 'voice'}
          onChange={e => onVoiceInputChange(e.target.checked)}
        />
        <span className="icon-box">
          <span className="fa">🎤</span>
        </span>
      </label>
      {/* 语音播报按钮 */}
      <label className="voice-toggle-label">
        <input
          type="checkbox"
          className="voice-toggle-input"
          checked={speechEnabled}
          onChange={e => onVoiceOutputChange(e.target.checked)}
        />
        <span className="icon-box">
          <span className="fa">🔊</span>
        </span>
      </label>
    </div>
  );
};

export default VoiceControls;