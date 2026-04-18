import React from 'react';
import '../css/neumorphism.css';

const NeumorphicPagination = ({ current, total, pageSize, onChange }) => {
  const pageCount = Math.ceil(total / pageSize);
  
  return (
    <div className="neumorphic-pagination">
      {Array.from({ length: pageCount }, (_, i) => i + 1).map(page => (
        <button
          key={page}
          className={`neumorphic-pagination-item ${current === page ? 'active' : ''}`}
          onClick={() => onChange(page)}
        >
          {page}
        </button>
      ))}
    </div>
  );
};

export default NeumorphicPagination