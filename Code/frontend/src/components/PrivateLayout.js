import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import UserContext from '../contexts/UserContext';
import { getMe } from '../service/user';

const PrivateLayout = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    getMe().then(res => {
      if (res && res.success && res.data) {
        console.log('user data', res.data);
        setUser(res.data);
      } else {
        localStorage.removeItem('token');
        navigate('/login');
      }
    }).catch(() => {
      localStorage.removeItem('token');
      navigate('/login');
    }).finally(() => setLoading(false));
  }, [navigate]);

  if (loading) return null;

  return (
    <UserContext.Provider value={user}>
      {children}
    </UserContext.Provider>
  );
};

export default PrivateLayout; 