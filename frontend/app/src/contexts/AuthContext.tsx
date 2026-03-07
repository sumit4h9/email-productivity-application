import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import { authAPI, User, LoginRequest, SignupRequest } from "@/lib/api";
import {
  setTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  setupAutoRefresh,
} from "@/lib/tokenManager";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const isAuthenticated = !!user && !!getAccessToken();

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      const token = getAccessToken();
      if (token) {
        try {
          const userData = await authAPI.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error("Failed to load user:", error);
          clearTokens();
        }
      }
      setIsLoading(false);
    };

    loadUser();
  }, []);

  // Setup auto-refresh
  useEffect(() => {
    if (!isAuthenticated) return;

    const cleanup = setupAutoRefresh(async () => {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          console.log("Attempting auto-refresh...");
          const response = await authAPI.autoRefresh(refreshToken);
          setTokens(
            response.access_token,
            response.refresh_token,
            response.expires_in
          );
          console.log("Auto-refresh successful");
        } catch (error) {
          console.error("Auto-refresh failed:", error);
          // Don't logout on auto-refresh failure, let the API interceptor handle it
          // The interceptor will attempt manual refresh on the next API call
        }
      } else {
        console.warn("No refresh token available for auto-refresh");
      }
    });

    return cleanup;
  }, [isAuthenticated]);

  const login = async (data: LoginRequest) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await authAPI.login(data);
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // Fetch user data after successful login
      const userData = await authAPI.getCurrentUser();
      setUser(userData);

      // Redirect to add-account for onboarding
      navigate("/add-account");
    } catch (err: unknown) {
      const maybe = err as { response?: { data?: { detail?: string } } };
      const errorMessage =
        maybe.response?.data?.detail || "Login failed. Please try again.";
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (data: SignupRequest) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await authAPI.signup(data);
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // Fetch user data after successful signup
      const userData = await authAPI.getCurrentUser();
      setUser(userData);

      // Redirect to add-account for onboarding
      navigate("/add-account");
    } catch (err: unknown) {
      const maybe = err as { response?: { data?: { detail?: string } } };
      const errorMessage =
        maybe.response?.data?.detail || "Signup failed. Please try again.";
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);

    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        await authAPI.logout(refreshToken);
      }
    } catch (error) {
      console.error("Logout error:", error);
      // Continue with local logout even if API call fails
    } finally {
      clearTokens();
      setUser(null);
      setIsLoading(false);
      navigate("/login");
    }
  };

  const refreshToken = async () => {
    const refreshTokenValue = getRefreshToken();
    if (!refreshTokenValue) {
      console.error("No refresh token available for manual refresh");
      clearTokens();
      setUser(null);
      navigate("/login");
      throw new Error("No refresh token available");
    }

    try {
      console.log("Attempting manual token refresh...");
      const response = await authAPI.refresh(refreshTokenValue);
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );
      console.log("Manual token refresh successful");
    } catch (err) {
      console.error("Manual token refresh failed:", err);
      clearTokens();
      setUser(null);
      navigate("/login");
      throw err;
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    signup,
    logout,
    refreshToken,
    error,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// HOC for protected routes
interface ProtectedRouteProps {
  children: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/login");
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : null;
};
