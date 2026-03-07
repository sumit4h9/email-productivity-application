import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "./tokenManager";

// Type declaration for Vite environment variables
// declare global {
//   interface ImportMeta {
//     readonly env: Record<string, string>;
//   }
// }

// API base URL - robust normalization around env misconfiguration
function resolveApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined;

  // If explicitly provided and already absolute (http/https), use it
  if (raw && /^https?:\/\//i.test(raw)) return raw.replace(/\/$/, "");

  // If provided as just a port like ":5000" or "5000", attach current host
  if (raw && (/^:\d+$/.test(raw) || /^\d+$/.test(raw))) {
    const port = raw.replace(/^:?/, "");
    return `${window.location.protocol}//${window.location.hostname}:${port}`;
  }

  // If provided as relative path like "/api" or "api", prefix current origin
  if (raw && !raw.startsWith("http")) {
    const path = raw.startsWith("/") ? raw : `/${raw}`;
    return `${window.location.origin}${path}`.replace(/\/$/, "");
  }

  // Fallback: assume backend on localhost:5000
  return "http://localhost:8000";
}

const API_BASE_URL = resolveApiBaseUrl();

// CSRF token management
const csrfToken: string | null = null;

const getCsrfToken = (): string | null => {
  // Try to get CSRF token from meta tag (if set by backend)
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute("content");
  }
  return csrfToken;
};

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Important for CORS with credentials
});

// Request interceptor to add auth token and CSRF protection
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add CSRF token for state-changing operations
    const csrfToken = getCsrfToken();
    if (
      csrfToken &&
      config.headers &&
      ["post", "put", "patch", "delete"].includes(
        config.method?.toLowerCase() || ""
      )
    ) {
      config.headers["X-CSRF-Token"] = csrfToken;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh and error handling
apiClient.interceptors.response.use(
  response => {
    // Check for new tokens from automatic refresh middleware
    const newAccessToken = response.headers["x-new-access-token"];
    const newRefreshToken = response.headers["x-new-refresh-token"];

    if (newAccessToken || newRefreshToken) {
      const currentAccessToken = getAccessToken();
      const currentRefreshToken = getRefreshToken();

      setTokens(
        newAccessToken || currentAccessToken || "",
        newRefreshToken || currentRefreshToken || ""
      );
      console.log("Received new tokens from server auto-refresh");
    }

    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
      _retryCount?: number;
    };

    // Handle 401 errors (unauthorized)
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

      // Prevent infinite retry loops
      if (originalRequest._retryCount > 2) {
        console.error("Too many refresh attempts, logging out");
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
          console.error("No refresh token available, logging out");
          clearTokens();
          window.location.href = "/login";
          return Promise.reject(error);
        }

        console.log("Attempting token refresh due to 401 error");

        // Try to refresh the token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        setTokens(access_token, refresh_token);
        console.log("Token refresh successful, retrying original request");

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);

        // Only logout if this is a definitive failure (not a network error)
        const error = refreshError as AxiosError;
        if (error.response?.status === 401 || error.response?.status === 403) {
          console.error("Refresh token invalid, logging out");
          clearTokens();
          window.location.href = "/login";
        } else {
          console.error("Network error during refresh, will retry later");
        }

        return Promise.reject(refreshError);
      }
    }

    // Handle other error responses
    if (error.response) {
      // Handle rate limiting (429)
      if (error.response.status === 429) {
        const retryAfter = error.response.headers["retry-after"];
        const rateLimitRemaining =
          error.response.headers["x-ratelimit-remaining"];
        console.warn(
          `Rate limited. Retry after: ${retryAfter}s, Remaining: ${rateLimitRemaining}`
        );

        // You could show a user-friendly message here
        // toast.error(`Too many requests. Please wait ${retryAfter} seconds.`);
      }

      // Server responded with error status
      const data = error.response.data as unknown as
        | { detail?: string }
        | undefined;
      const errorMessage = data?.detail || "An error occurred";
      console.error("API Error:", errorMessage);
    } else if (error.request) {
      // Request made but no response received
      console.error("Network Error:", "No response from server");
    } else {
      // Error in setting up the request
      console.error("Request Error:", error.message);
    }

    return Promise.reject(error);
  }
);

// Type definitions for API responses
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface SignupRequest {
  email: string;
  password: string;
  username: string;
}

export type LoginRequest = (
  | { email: string; username?: never }
  | { username: string; email?: never }
) & { password: string };

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  status: string;
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface ResetPasswordResponse {
  status: string;
  message: string;
}
// OAuth interfaces
export interface OAuthUrlResponse {
  authorization_url: string;
}

export interface OAuthCallbackRequest {
  code: string;
}

export interface OAuthCallbackResponse {
  account_id: string;
  provider: string;
  account_email: string;
  status: string;
  sync_task_id: string;
  message: string;
}

export interface ConnectedAccountResponse {
  id: string;
  provider: string;
  account_email: string;
  last_synced_at: string | null;
  sync_status: string;
  is_active: boolean;
  created_at: string;
}

export interface AccountListResponse {
  accounts: ConnectedAccountResponse[];
}

export interface AccountStatusResponse {
  id: string;
  provider: string;
  account_email: string;
  sync_status: string;
  last_synced_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DisconnectResponse {
  message: string;
}

// New verification interfaces
export interface VerificationResponse {
  status: string;
  contact: string;
  message: string;
}

export interface VerificationSuccessResponse {
  status: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface SignupInitRequest {
  email: string;
  username: string;
  password: string;
}

export interface SignupVerifyRequest {
  email: string;
  code: string;
}

export interface LoginInitRequest {
  email_or_username: string;
  password: string;
}

export interface LoginVerifyRequest {
  email_or_username: string;
  code: string;
}

// API endpoint functions
export const authAPI = {
  signup: async (data: SignupRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/signup", data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  autoRefresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/auto-refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },

  forgotPassword: async (
    data: ForgotPasswordRequest
  ): Promise<ForgotPasswordResponse> => {
    const response = await apiClient.post<ForgotPasswordResponse>(
      "/auth/forgot",
      data
    );
    return response.data;
  },

  resetPassword: async (
    data: ResetPasswordRequest
  ): Promise<ResetPasswordResponse> => {
    const response = await apiClient.post<ResetPasswordResponse>(
      "/auth/reset",
      data
    );
    return response.data;
  },

  // New verification endpoints
  signupInit: async (
    data: SignupInitRequest
  ): Promise<VerificationResponse> => {
    const response = await apiClient.post<VerificationResponse>(
      "/auth/signup/init",
      data
    );
    return response.data;
  },

  signupVerify: async (
    data: SignupVerifyRequest
  ): Promise<VerificationSuccessResponse> => {
    const response = await apiClient.post<VerificationSuccessResponse>(
      "/auth/signup/verify",
      data
    );
    return response.data;
  },

  loginInit: async (data: LoginInitRequest): Promise<VerificationResponse> => {
    const response = await apiClient.post<VerificationResponse>(
      "/auth/login/init",
      data
    );
    return response.data;
  },

  loginVerify: async (
    data: LoginVerifyRequest
  ): Promise<VerificationSuccessResponse> => {
    const response = await apiClient.post<VerificationSuccessResponse>(
      "/auth/login/verify",
      data
    );
    return response.data;
  },
};

// OAuth API functions
export const oauthAPI = {
  getGoogleUrl: async (): Promise<OAuthUrlResponse> => {
    const response = await apiClient.get<OAuthUrlResponse>(
      "/api/v1/oauth/google/url"
    );
    return response.data;
  },

  googleCallback: async (code: string): Promise<OAuthCallbackResponse> => {
    const response = await apiClient.post<OAuthCallbackResponse>(
      "/api/v1/oauth/google/callback",
      { code }
    );
    return response.data;
  },

  listAccounts: async (): Promise<AccountListResponse> => {
    const response = await apiClient.get<AccountListResponse>(
      "/api/v1/oauth/accounts"
    );
    return response.data;
  },

  getAccountStatus: async (
    accountId: string
  ): Promise<AccountStatusResponse> => {
    const response = await apiClient.get<AccountStatusResponse>(
      `/api/v1/oauth/accounts/${accountId}/status`
    );
    return response.data;
  },

  disconnectAccount: async (accountId: string): Promise<DisconnectResponse> => {
    const response = await apiClient.delete<DisconnectResponse>(
      `/api/v1/oauth/accounts/${accountId}`
    );
    return response.data;
  },
};

export default apiClient;
