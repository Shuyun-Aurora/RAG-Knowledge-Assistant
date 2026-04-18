import { Tabs } from 'antd';
import styled from 'styled-components';

const StyledTabs = styled(Tabs)`
  &.ant-tabs {
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
    min-width: 320px;
    
    .ant-tabs-nav {
      margin-bottom: 0;
      
      &::before {
        border-bottom: 1px solid #f0f0f0 !important;
      }
      
      .ant-tabs-tab {
        padding: 16px 24px; /* 增大内边距 */
        font-size: 16px;
        font-weight: 600; /* 默认加粗 */
        color: #666;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1); /* 平滑过渡 */
        border-radius: 8px 8px 0 0; /* 顶部圆角 */
        
        &:hover {
          color: #333;
          background: rgba(0, 0, 0, 0.03); /* 悬停背景色 */
        }
        
        .ant-tabs-tab-btn {
          font-size: inherit;
          font-weight: inherit;
          letter-spacing: 0.5px; /* 字间距微调 */
        }
      }
      
      .ant-tabs-tab-active {
        .ant-tabs-tab-btn {
          color: #222; /* 更深文字色 */
          font-weight: 700; /* 激活态更粗 */
        }
      }
      
      .ant-tabs-ink-bar {
        height: 2px; /* 加粗指示条 */
        border-radius: 2px 2px 0 0; /* 更大圆角 */
        background: linear-gradient(90deg, #222 0%, #444 100%); /* 渐变效果 */
      }
    }
  }
`;

export default StyledTabs;