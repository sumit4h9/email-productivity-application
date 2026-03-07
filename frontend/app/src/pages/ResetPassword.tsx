import React, { useState, useEffect } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ErrorDisplay } from "@/components/ui/error-display";
import { useResetPassword } from "@/hooks/useAuthHooks";
import { useToast } from "@/hooks/use-toast";
import { Eye, EyeOff } from "lucide-react";
import { sanitizePassword } from "@/lib/security";
import { validatePassword } from "@/lib/validation";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  const resetPasswordMutation = useResetPassword();
  const { toast } = useToast();

  // Check if token is present
  useEffect(() => {
    if (!token) {
      toast({
        title: "Invalid Reset Link",
        description: "This password reset link is invalid or has expired.",
        variant: "destructive",
      });
      navigate("/forgot-password");
    }
  }, [token, navigate, toast]);

  // Password strength validation
  const getPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (password.length >= 16) strength++;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSymbol = /[^A-Za-z0-9]/.test(password);
    const charTypes = [hasUpper, hasLower, hasNumber, hasSymbol];
    const charTypeCount = charTypes.filter(Boolean).length;
    if (charTypeCount >= 2) strength++;
    if (charTypeCount >= 3) strength++;
    return Math.min(strength, 5);
  };

  const getStrengthColor = (strength: number) => {
    if (strength <= 2) return "bg-red-500";
    if (strength <= 3) return "bg-yellow-500";
    if (strength <= 4) return "bg-blue-500";
    return "bg-green-500";
  };

  const getStrengthText = (strength: number) => {
    if (strength <= 2) return "Weak";
    if (strength <= 3) return "Fair";
    if (strength <= 4) return "Good";
    return "Strong";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError("");
    setConfirmPasswordError("");

    // Basic validation
    if (!newPassword.trim()) {
      setPasswordError("Password is required");
      return;
    }

    if (!confirmPassword.trim()) {
      setConfirmPasswordError("Please confirm your password");
      return;
    }

    if (newPassword !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match");
      return;
    }

    // Sanitize and validate password
    try {
      const sanitizedPassword = sanitizePassword(newPassword);
      const { isValid, message } = validatePassword(sanitizedPassword);

      if (!isValid) {
        setPasswordError(message);
        return;
      }

      // Submit to backend
      await resetPasswordMutation.mutateAsync({
        token: token!,
        new_password: sanitizedPassword,
        confirm_password: sanitizedPassword,
      });
    } catch (error) {
      // Error handling is done in the mutation hook
      console.error("Reset password error:", error);
    }
  };

  if (!token) {
    return null; // Will redirect in useEffect
  }

  const passwordStrength = getPasswordStrength(newPassword);

  return (
    <div className="flex min-h-screen">
      <div className="flex flex-1 flex-col justify-center py-8 px-4 sm:px-6 lg:flex-none lg:px-16 xl:px-20">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div>
            <div className="flex items-center mb-6">
              <div className="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center mr-3">
                <span className="material-icons text-white text-2xl">
                  all_infinite
                </span>
              </div>
              <h1 className="text-2xl font-extrabold text-gray-900">Axnore</h1>
            </div>
            <h2 className="mt-4 text-3xl font-extrabold tracking-tighter text-gray-900">
              Reset Your Password
            </h2>
            <p className="mt-2 text-base text-gray-600">
              Enter your new password below to complete the reset process.
            </p>
          </div>

          <div className="mt-6">
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <Label
                  htmlFor="newPassword"
                  className="block text-sm font-semibold text-gray-900"
                >
                  New Password
                </Label>
                <div className="mt-1 relative">
                  <Input
                    id="newPassword"
                    name="newPassword"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    placeholder="Enter your new password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    className={
                      passwordError
                        ? "border-red-500 focus:border-red-500 focus:ring-red-500 pr-10"
                        : "pr-10"
                    }
                    disabled={resetPasswordMutation.isPending}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {passwordError && <ErrorDisplay error={passwordError} />}

                {/* Password Strength Indicator */}
                {newPassword && (
                  <div className="mt-2">
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${getStrengthColor(passwordStrength)}`}
                          style={{ width: `${(passwordStrength / 5) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">
                        {getStrengthText(passwordStrength)}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <Label
                  htmlFor="confirmPassword"
                  className="block text-sm font-semibold text-gray-900"
                >
                  Confirm New Password
                </Label>
                <div className="mt-1 relative">
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    placeholder="Confirm your new password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    className={
                      confirmPasswordError
                        ? "border-red-500 focus:border-red-500 focus:ring-red-500 pr-10"
                        : "pr-10"
                    }
                    disabled={resetPasswordMutation.isPending}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {confirmPasswordError && (
                  <ErrorDisplay error={confirmPasswordError} />
                )}
              </div>

              <div>
                <button
                  className={`flex w-full justify-center rounded-lg border border-transparent py-2.5 px-4 text-base font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 ${
                    resetPasswordMutation.isPending
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-gray-900 hover:bg-gray-800"
                  }`}
                  disabled={resetPasswordMutation.isPending}
                  type="submit"
                >
                  {resetPasswordMutation.isPending
                    ? "Resetting..."
                    : "Reset Password"}
                </button>
              </div>
            </form>
          </div>

          <p className="mt-6 text-center text-sm text-gray-600">
            Remember your password?{" "}
            <Link
              className="font-semibold text-indigo-600 hover:text-indigo-500"
              to="/login"
            >
              Return to log in
            </Link>
          </p>
        </div>
      </div>

      <div className="relative hidden w-0 flex-1 lg:block pattern-bg overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/30 via-slate-900/50 to-purple-900/30"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-center p-8 relative z-10">
            <h2 className="text-4xl font-black tracking-tighter mb-3 text-shadow">
              Secure Your Account
            </h2>
            <p className="text-lg text-slate-200 max-w-md mx-auto text-shadow">
              Create a strong password to protect your AI-powered dashboard and
              keep your data secure.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
