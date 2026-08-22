import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Index from "@/pages/Index";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";
import VerifySignup from "@/pages/VerifySignup";
import VerifyLogin from "@/pages/VerifyLogin";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import Dashboard from "@/pages/Dashboard";
import AuthConnect from "@/pages/AuthConnect";
import AppleConnect from "@/pages/AppleConnect";
import AddAccount from "@/pages/AddAccount";
import GoogleOAuthCallback from "@/pages/GoogleOAuthCallback";
import NotFound from "@/app/Not-found";
import { useIsAuthenticated } from "./hooks/useAuthHooks";
import { ReactNode } from "react";
import { Loader2 } from "lucide-react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Protected Route wrapper component
const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading } = useIsAuthenticated();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route wrapper (redirect to dashboard if already authenticated)
const PublicRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading } = useIsAuthenticated();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return !isAuthenticated ? (
    <>{children}</>
  ) : (
    <Navigate to="/add-account" replace />
  );
};

// App Routes component
const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Index />} />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        }
      />
      <Route
        path="/verify-signup"
        element={
          <PublicRoute>
            <VerifySignup />
          </PublicRoute>
        }
      />
      <Route
        path="/verify-login"
        element={
          <PublicRoute>
            <VerifyLogin />
          </PublicRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <ForgotPassword />
          </PublicRoute>
        }
      />
      <Route
        path="/reset-password"
        element={
          <PublicRoute>
            <ResetPassword />
          </PublicRoute>
        }
      />
      <Route
        path="/add-account"
        element={
          <ProtectedRoute>
            <AddAccount />
          </ProtectedRoute>
        }
      />
      <Route
        path="/connect/apple"
        element={
          <PublicRoute>
            <AppleConnect />
          </PublicRoute>
        }
      />
      <Route
        path="/auth-connect"
        element={
          <ProtectedRoute>
            <AuthConnect />
          </ProtectedRoute>
        }
      />
      <Route
        path="/apple-connect"
        element={
          <ProtectedRoute>
            <AppleConnect />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route path="/auth/google/callback" element={<GoogleOAuthCallback />} />
      {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
