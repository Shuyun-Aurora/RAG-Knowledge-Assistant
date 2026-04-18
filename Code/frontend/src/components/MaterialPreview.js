import React, { useState } from 'react';
import { Button, Modal, Spin } from 'antd';
import { BASEURL } from '../service/common';
import '../css/preview.css';

const MaterialPreview = ({
  materials,
  loading,
  selectedFile,
  onFileSelect,
  onPreview
}) => {
  const [previewFile, setPreviewFile] = useState(null);
  const [previewVisible, setPreviewVisible] = useState(false);

  const handlePreview = (file) => {
    setPreviewFile(file);
    setPreviewVisible(true);
  };

  const handlePreviewClose = () => {
    setPreviewVisible(false);
    setPreviewFile(null);
  };

  // 可取消的单选逻辑
  const handleSelect = (fileId) => {
    if (selectedFile === fileId) {
      onFileSelect(null, false); // 取消选中
    } else {
      onFileSelect(fileId, true); // 选中
    }
  };

  return (
    <>
      <Spin spinning={loading}>
        <div className="neumorphic-card" style={{ padding: 24, marginBottom: 16 }}>
          <div className="material-radio-group">
            {materials.map(item => (
              <div key={item.file_id} className="material-radio-row">
                <div className="material-radio-label-wrap">
                  <input
                    type="checkbox"
                    id={`material-radio-${item.file_id}`}
                    className="material-radio-input"
                    checked={selectedFile === item.file_id}
                    onChange={() => handleSelect(item.file_id)}
                    name="material-radio"
                  />
                  <label
                    htmlFor={`material-radio-${item.file_id}`}
                    className="material-radio-label"
                  >
                    <span className="material-radio-circle" />
                    <span className="material-radio-text">{item.filename}</span>
                  </label>
                </div>
                <Button
                  className="neumorphic-btn"
                  size="small"
                  onClick={() => handlePreview(item)}
                  style={{ minWidth: 60 }}
                >
                  预览
                </Button>
              </div>
            ))}
          </div>
        </div>
      </Spin>
      <Modal
        className="neumorphic-modal"
        open={previewVisible}
        title={previewFile?.filename}
        footer={null}
        onCancel={handlePreviewClose}
        width={800}
        styles={{ body: { minHeight: 500, padding: 0 } }}
        forceRender
      >
        {previewFile?.file_id && (
          <iframe
            key={previewFile.file_id}
            src={`${BASEURL}/api/rag/preview/${previewFile.file_id}`}
            style={{ width: '100%', height: '80vh', border: 'none' }}
            title="课件预览"
          />
        )}
      </Modal>
    </>
  );
};

export default MaterialPreview;
