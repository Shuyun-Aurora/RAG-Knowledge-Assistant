import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import AppRouter from './components/AppRouter';
import NetworkStatus from './components/NetworkStatus';
import './css/global.css';

function App() {
  return (
    <ConfigProvider>
      <Router>
        <NetworkStatus />
        <AppRouter />
      </Router>
    </ConfigProvider>
  );
}

export default App;
