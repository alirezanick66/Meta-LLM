import axios from 'axios';

// ساخت instance از axios با تنظیمات پایه
const api = axios.create({
  baseURL: '/api', // به خاطر proxy در vite.config
  timeout: 30000, // 30 ثانیه
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor برای لاگ کردن requests (فقط در dev)
if (import.meta.env.DEV) {
  api.interceptors.request.use(
    (config) => {
      console.log('🚀 API Request:', config.method.toUpperCase(), config.url);
      return config;
    },
    (error) => {
      console.error('❌ Request Error:', error);
      return Promise.reject(error);
    }
  );

  api.interceptors.response.use(
    (response) => {
      console.log('✅ API Response:', response.status, response.config.url);
      return response;
    },
    (error) => {
      console.error('❌ Response Error:', error.response?.status, error.message);
      return Promise.reject(error);
    }
  );
}

/**
 * ارسال سوال به API
 * @param {string} query - سوال کاربر
 * @param {number} temperature - میزان خلاقیت (0-2)
 * @returns {Promise} - پاسخ API
 */
export const sendMessage = async (query, temperature = 0.3) => {
  try {
    const response = await api.post('/chat', {
      query,
      temperature,
    });
    return response.data;
  } catch (error) {
    // مدیریت خطاها
    if (error.response) {
      // سرور پاسخ داده ولی با error
      throw {
        message: error.response.data.error || 'خطا در دریافت پاسخ از سرور',
        status: error.response.status,
      };
    } else if (error.request) {
      // درخواست فرستاده شده ولی پاسخی نیومده
      throw {
        message: 'سرور پاسخگو نیست. لطفاً اتصال اینترنت خود را بررسی کنید.',
        status: 0,
      };
    } else {
      // خطای دیگه
      throw {
        message: error.message || 'خطای نامشخص رخ داده است',
        status: -1,
      };
    }
  }
};

/**
 * دریافت آمار سیستم
 * @returns {Promise} - آمار سیستم
 */
export const getStats = async () => {
  try {
    const response = await api.get('/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
};

/**
 * بررسی وضعیت سلامت سرور
 * @returns {Promise} - وضعیت health
 */
export const checkHealth = async () => {
  try {
    const response = await axios.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

export default api;