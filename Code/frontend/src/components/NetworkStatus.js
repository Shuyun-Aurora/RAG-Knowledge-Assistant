import React, { useState, useEffect } from 'react';
import { Alert } from 'antd';
import { API_PREFIX, REQUEST_CONFIG } from '../config/network';

const NetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [backendAvailable, setBackendAvailable] = useState(false); // 初始状态设为 false
  const [retrying, setRetrying] = useState(false);
  const [initialCheckDone, setInitialCheckDone] = useState(false);

  // 检查后端服务是否可用
  const checkBackendStatus = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时

      const response = await fetch(`${API_PREFIX}/health`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      const newStatus = response.ok;
      setBackendAvailable(newStatus);
      
      if (newStatus && !backendAvailable && initialCheckDone) {
        window.location.reload(); // 仅在初始检查后且状态改变时刷新
      }
    } catch (error) {
      setBackendAvailable(false);
    } finally {
      setInitialCheckDone(true);
    }
  };

  // 自动重试连接后端
  useEffect(() => {
    let retryInterval;
    
    if (!backendAvailable && isOnline) {
      setRetrying(true);
      // 立即执行一次检查
      checkBackendStatus();
      // 然后设置定时检查
      retryInterval = setInterval(checkBackendStatus, REQUEST_CONFIG.HEALTH_CHECK_INTERVAL);
    }

    return () => {
      if (retryInterval) {
        clearInterval(retryInterval);
      }
    };
  }, [backendAvailable, isOnline]);

  // 监听网络状态变化
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      checkBackendStatus();
    };

    const handleOffline = () => {
      setIsOnline(false);
      setBackendAvailable(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 初始检查
    checkBackendStatus();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // 在组件挂载时立即检查一次
  useEffect(() => {
    checkBackendStatus();
  }, []);

  if (!isOnline) {
    return (
      <Alert
        message="网络连接已断开"
        description="请检查您的网络连接。系统将在网络恢复后自动重连。"
        type="error"
        showIcon
        banner
      />
    );
  }

  if (!backendAvailable && initialCheckDone) {
    return (
      <Alert
        message="服务器连接失败"
        description={retrying ? "正在尝试重新连接服务器..." : "无法连接到服务器，请稍后再试。"}
        type="warning"
        showIcon
        banner
      />
    );
  }

  return null;
};

export default NetworkStatus; 