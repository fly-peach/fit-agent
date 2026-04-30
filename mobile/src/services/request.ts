import axios from 'axios';
import { API_BASE_URL } from '../constants';
import { storage } from '../utils/storage';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await storage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const { code, message: msg, data } = response.data;
    if (code === 200) return data;
    if (code === undefined && data === undefined) return response.data;
    return Promise.reject(new Error(msg || '请求失败'));
  },
  (error) => {
    if (error.response?.status === 401) {
      storage.removeItem('token');
    }
    return Promise.reject(error);
  }
);

export default api;
