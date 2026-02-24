import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// Define response data structure
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
}

// Define error structure
export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}

// Configuration interface
interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

class ApiClient {
  private client: AxiosInstance;
  private static instance: ApiClient;

  constructor(config: ApiClientConfig = {}) {
    this.client = axios.create({
      baseURL: config.baseURL || (typeof window !== 'undefined' && (window as any).REACT_APP_API_BASE_URL) || 'http://localhost:5000',
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
    });

    this.setupInterceptors();
  }

  // Singleton pattern to ensure single instance
  public static getInstance(config?: ApiClientConfig): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient(config);
    }
    return ApiClient.instance;
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Log request in development
        if ((typeof window !== 'undefined' && (window as any).NODE_ENV === 'development')) {
          console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`, config);
        }

        return config;
      },
      (error) => {
        console.error('🚨 Request Interceptor Error:', error);
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response in development
        if ((typeof window !== 'undefined' && (window as any).NODE_ENV === 'development')) {
          console.log(`✅ API Response: ${response.status} ${response.config.url}`, response.data);
        }

        return response;
      },
      (error: AxiosError) => {
        console.error('🚨 Response Interceptor Error:', error);

        // Handle specific error cases
        if (error.response) {
          // Server responded with error status
          const status = error.response.status;
          const message = this.getErrorMessage(error);

          switch (status) {
            case 401:
              this.handleUnauthorized();
              break;
            case 403:
              console.error('Access forbidden');
              break;
            case 404:
              console.error('Resource not found');
              break;
            case 500:
              console.error('Internal server error');
              break;
            default:
              console.error(`HTTP error ${status}`);
          }

          return Promise.reject(this.handleError(error));
        } else if (error.request) {
          // Request was made but no response received
          console.error('No response received:', error.request);
          return Promise.reject({
            message: 'Network error: Unable to connect to server',
            status: 0,
            code: 'NETWORK_ERROR',
          } as ApiError);
        } else {
          // Something else happened
          console.error('Request setup error:', error.message);
          return Promise.reject({
            message: error.message,
            status: 0,
            code: 'REQUEST_ERROR',
          } as ApiError);
        }
      }
    );
  }

  private getAuthToken(): string | null {
    // Get token from localStorage or your auth context
    return localStorage.getItem('auth_token') || 
           sessionStorage.getItem('auth_token') || 
           null;
  }

  private handleUnauthorized(): void {
    // Clear auth tokens
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
    
    // Redirect to login page if not already there
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  private getErrorMessage(error: AxiosError): string {
    if (error.response?.data) {
      const data = error.response.data as any;
      return data.message || data.error || data.detail || 'An error occurred';
    }
    return error.message || 'An unexpected error occurred';
  }

  private handleError(error: AxiosError): ApiError {
    return {
      message: this.getErrorMessage(error),
      status: error.response?.status || 0,
      code: error.code,
      details: error.response?.data,
    };
  }

  // HTTP Methods
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // File upload method
  public async upload<T = any>(
    url: string, 
    formData: FormData, 
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(Math.round(progress));
        }
      },
    };

    const response = await this.client.post<T>(url, formData, config);
    return response.data;
  }

  // Set authentication token
  public setAuthToken(token: string, persist: boolean = true): void {
    if (persist) {
      localStorage.setItem('auth_token', token);
    } else {
      sessionStorage.setItem('auth_token', token);
    }
  }

  // Clear authentication token
  public clearAuthToken(): void {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  }

  // Update base URL
  public setBaseURL(baseURL: string): void {
    this.client.defaults.baseURL = baseURL;
  }

  // Update default headers
  public setHeader(key: string, value: string): void {
    this.client.defaults.headers.common[key] = value;
  }

  // Remove header
  public removeHeader(key: string): void {
    delete this.client.defaults.headers.common[key];
  }
}

// Create and export default instance
const apiClient = ApiClient.getInstance();

export default apiClient;