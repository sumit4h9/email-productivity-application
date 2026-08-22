import {
  useMutation,
  useQuery,
  useQueryClient,
  UseMutationResult,
  UseQueryResult,
} from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  authAPI,
  LoginRequest,
  SignupRequest,
  User,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  TokenResponse,
} from "@/lib/api";
import {
  setTokens,
  getRefreshToken,
  clearTokens,
  getAccessToken,
} from "@/lib/tokenManager";
import { useToast } from "@/hooks/use-toast";

// Query keys
const queryKeys = {
  user: ["user"] as const,
  currentUser: ["user", "current"] as const,
};

// Hook for signup
export const useSignup = (): UseMutationResult<
  TokenResponse,
  unknown,
  SignupRequest,
  unknown
> => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: SignupRequest) => authAPI.signup(data),
    onSuccess: async response => {
      // Store tokens
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // Invalidate and refetch user data
      await queryClient.invalidateQueries({ queryKey: queryKeys.user });

      toast({
        title: "Account created successfully!",
        description: "Welcome to Axnore!",
      });

      navigate("/add-account");
    },
    onError: (err: unknown) => {
      const maybe = err as {
        response?: { status?: number; data?: { detail?: unknown } };
      };
      let errorMessage = "Signup failed. Please try again.";

      if (maybe.response?.status === 422) {
        // Validation error - show detailed message
        const detail = maybe.response.data?.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const errorMessages = detail
            .map(
              (error: { loc?: string[]; msg?: string }) =>
                `${error.loc?.join(".") || "unknown"}: ${error.msg || "Unknown error"}`
            )
            .join(", ");
          errorMessage = `Validation error: ${errorMessages}`;
        } else if (typeof detail === "string") {
          errorMessage = detail;
        }
      } else if (maybe.response?.status === 400) {
        errorMessage =
          typeof maybe.response.data?.detail === "string"
            ? maybe.response.data.detail
            : "Invalid request data";
      } else if (maybe.response?.data?.detail) {
        errorMessage = String(maybe.response.data.detail);
      }

      toast({
        title: "Signup Failed",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });
};

// Hook for login
export const useLogin = (): UseMutationResult<
  TokenResponse,
  unknown,
  LoginRequest,
  unknown
> => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: LoginRequest) => authAPI.login(data),
    onSuccess: async response => {
      // Store tokens
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // Invalidate and refetch user data
      await queryClient.invalidateQueries({ queryKey: queryKeys.user });

      toast({
        title: "Welcome back!",
        description: "You have successfully logged in.",
      });

      navigate("/add-account");
    },
    onError: (err: unknown) => {
      const maybe = err as {
        response?: { status?: number; data?: { detail?: unknown } };
      };
      let errorMessage = "Login failed. Please check your credentials.";

      if (maybe.response?.status === 422) {
        // Validation error - show detailed message
        const detail = maybe.response.data?.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const errorMessages = detail
            .map(
              (error: { loc?: string[]; msg?: string }) =>
                `${error.loc?.join(".") || "unknown"}: ${error.msg || "Unknown error"}`
            )
            .join(", ");
          errorMessage = `Validation error: ${errorMessages}`;
        } else if (typeof detail === "string") {
          errorMessage = detail;
        }
      } else if (maybe.response?.status === 400) {
        errorMessage =
          typeof maybe.response.data?.detail === "string"
            ? maybe.response.data.detail
            : "Invalid request data";
      } else if (maybe.response?.data?.detail) {
        errorMessage = String(maybe.response.data.detail);
      }

      toast({
        title: "Login Failed",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });
};

// Hook for logout
export const useLogout = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        await authAPI.logout(refreshToken);
      }
    },
    onSuccess: () => {
      // Clear tokens
      clearTokens();

      // Clear all queries
      queryClient.clear();

      toast({
        title: "Logged out",
        description: "You have been successfully logged out.",
      });

      navigate("/login");
    },
    onError: err => {
      console.error("Logout error:", err);
      // Still clear tokens and redirect even if API call fails
      clearTokens();
      queryClient.clear();
      navigate("/login");
    },
  });
};

// Hook for auto-refresh
export const useAutoRefresh = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        throw new Error("No refresh token available");
      }
      return authAPI.autoRefresh(refreshToken);
    },
    onSuccess: response => {
      // Update tokens
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // Invalidate user queries to ensure fresh data
      queryClient.invalidateQueries({ queryKey: queryKeys.user });
    },
    onError: err => {
      console.error("Auto-refresh failed:", err);
      // Don't clear tokens on auto-refresh failure
      // Let manual refresh handle the error
    },
  });
};

// Hook for manual token refresh
export const useRefreshToken = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        throw new Error("No refresh token available");
      }
      return authAPI.refresh(refreshToken);
    },
    onSuccess: response => {
      // Update tokens
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // Invalidate user queries
      queryClient.invalidateQueries({ queryKey: queryKeys.user });
    },
    onError: err => {
      console.error("Token refresh failed:", err);

      // Clear tokens and redirect to login
      clearTokens();
      queryClient.clear();

      toast({
        title: "Session expired",
        description: "Please log in again.",
        variant: "destructive",
      });

      navigate("/login");
    },
  });
};

// Hook to get current user
export const useCurrentUser = (): UseQueryResult<User, unknown> => {
  const navigate = useNavigate();
  const { toast } = useToast();

  return useQuery<User>({
    queryKey: queryKeys.currentUser,
    queryFn: authAPI.getCurrentUser,
    enabled: !!getAccessToken(), // Only run if we have a token
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
    retry: (failureCount, error: unknown) => {
      const maybe = error as { response?: { status?: number } };
      // Don't retry on 401 errors
      if (maybe?.response?.status === 401) {
        return false;
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
    meta: {
      onError: (err: unknown) => {
        const maybe = err as { response?: { status?: number } };
        const status = maybe?.response?.status;

        if (status === 401) {
          // Unauthorized, clear tokens and redirect
          clearTokens();
          navigate("/login");

          toast({
            title: "Session expired",
            description: "Please log in again.",
            variant: "destructive",
          });
        } else {
          toast({
            title: "Error",
            description: "Failed to load user data.",
            variant: "destructive",
          });
        }
      },
    },
  });
};

// Hook to check if user is authenticated
export const useIsAuthenticated = () => {
  const { data: user, isLoading } = useCurrentUser();
  const token = getAccessToken();

  return {
    isAuthenticated: !!user && !!token,
    user,
    isLoading,
  };
};

// Hook for forgot password
export const useForgotPassword = () => {
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: ForgotPasswordRequest) => authAPI.forgotPassword(data),
    onSuccess: () => {
      toast({
        title: "Reset link sent!",
        description:
          "If this email exists, you will receive a password reset link.",
      });
    },
    onError: (err: unknown) => {
      const maybe = err as {
        response?: { status?: number; data?: { detail?: unknown } };
      };
      let errorMessage = "Failed to send reset link. Please try again.";

      if (maybe.response?.status === 429) {
        errorMessage = "Too many requests. Please wait before trying again.";
      } else if (maybe.response?.data?.detail) {
        errorMessage = String(maybe.response.data.detail);
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });
};

// Hook for reset password
export const useResetPassword = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: ResetPasswordRequest) => authAPI.resetPassword(data),
    onSuccess: () => {
      toast({
        title: "Password reset successful!",
        description:
          "Your password has been reset. Please log in with your new password.",
      });
      navigate("/login");
    },
    onError: (err: unknown) => {
      const maybe = err as {
        response?: { status?: number; data?: { detail?: unknown } };
      };
      let errorMessage = "Failed to reset password. Please try again.";

      if (maybe.response?.status === 400) {
        errorMessage =
          "Invalid or expired reset token. Please request a new reset link.";
      } else if (maybe.response?.status === 429) {
        errorMessage = "Too many requests. Please wait before trying again.";
      } else if (maybe.response?.data?.detail) {
        errorMessage = String(maybe.response.data.detail);
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });
};
