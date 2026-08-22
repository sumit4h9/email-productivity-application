// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";

// Token storage functions with error handling
export const setTokens = (
  accessToken: string,
  refreshToken: string,
  expiresIn: number = 1800
) => {
  try {
    // Store tokens in localStorage for persistence
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);

    // Calculate and store expiry time
    const expiryTime = Date.now() + expiresIn * 1000;
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
  } catch (error) {
    console.error("Error storing tokens:", error);
    // Fallback to sessionStorage if localStorage is not available
    try {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
      sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      const expiryTime = Date.now() + expiresIn * 1000;
      sessionStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    } catch (sessionError) {
      console.error("Error storing tokens in sessionStorage:", sessionError);
    }
  }
};

export const getAccessToken = (): string | null => {
  try {
    // Check if token has expired
    const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (expiryTime && Date.now() > parseInt(expiryTime)) {
      // Token has expired, but don't return null immediately
      // Let the auto-refresh system handle it
      console.warn("Access token has expired, auto-refresh should handle this");
    }

    return (
      localStorage.getItem(ACCESS_TOKEN_KEY) ||
      sessionStorage.getItem(ACCESS_TOKEN_KEY)
    );
  } catch (error) {
    console.error("Error retrieving access token:", error);
    return null;
  }
};

export const getRefreshToken = (): string | null => {
  try {
    return (
      localStorage.getItem(REFRESH_TOKEN_KEY) ||
      sessionStorage.getItem(REFRESH_TOKEN_KEY)
    );
  } catch (error) {
    console.error("Error retrieving refresh token:", error);
    return null;
  }
};

export const clearTokens = () => {
  try {
    // Clear from localStorage
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);

    // Clear from sessionStorage
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_EXPIRY_KEY);
  } catch (error) {
    console.error("Error clearing tokens:", error);
  }
};

export const isTokenExpired = (): boolean => {
  try {
    const expiryTime =
      localStorage.getItem(TOKEN_EXPIRY_KEY) ||
      sessionStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiryTime) {
      return true; // No expiry time means token is expired or doesn't exist
    }
    return Date.now() > parseInt(expiryTime);
  } catch (error) {
    console.error("Error checking token expiry:", error);
    return true; // Assume expired if error
  }
};

export const getTokenTimeRemaining = (): number => {
  try {
    const expiryTime =
      localStorage.getItem(TOKEN_EXPIRY_KEY) ||
      sessionStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiryTime) {
      return 0;
    }
    const remaining = parseInt(expiryTime) - Date.now();
    return remaining > 0 ? remaining : 0;
  } catch (error) {
    console.error("Error calculating token time remaining:", error);
    return 0;
  }
};

// Auto-refresh setup
export const setupAutoRefresh = (onRefresh: () => Promise<void>) => {
  let isRefreshing = false;

  const checkAndRefresh = async () => {
    if (isRefreshing) {
      return; // Prevent multiple simultaneous refresh attempts
    }

    const timeRemaining = getTokenTimeRemaining();

    // Refresh when 10 minutes or less remaining (more aggressive refresh)
    if (timeRemaining > 0 && timeRemaining <= 10 * 60 * 1000) {
      isRefreshing = true;
      try {
        console.log(
          `Auto-refreshing token, ${Math.round(timeRemaining / 60000)} minutes remaining`
        );
        await onRefresh();
        console.log("Auto-refresh completed successfully");
      } catch (error) {
        console.error("Auto-refresh failed:", error);
        // Don't logout immediately, let the API interceptor handle it
      } finally {
        isRefreshing = false;
      }
    }
  };

  // Check every 30 seconds for more responsive refresh
  const intervalId = setInterval(checkAndRefresh, 30000);

  // Initial check
  checkAndRefresh();

  // Return cleanup function
  return () => clearInterval(intervalId);
};
