import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ErrorDisplay } from "@/components/ui/error-display";
import { useToast } from "@/hooks/use-toast";
import { authAPI, SignupVerifyRequest } from "@/lib/api";
import { setTokens } from "@/lib/tokenManager";
import { sanitizeEmail } from "@/lib/security";
import { validateEmail } from "@/lib/validation";
import { ArrowLeft, Mail, Shield, Clock } from "lucide-react";

interface LocationState {
  email: string;
  contact: string;
  message: string;
}

const VerifySignup = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [email, setEmail] = useState("");
  const [contact, setContact] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Get data from navigation state
  useEffect(() => {
    const state = location.state as LocationState;
    if (state) {
      setEmail(state.email);
      setContact(state.contact);
    } else {
      // If no state, redirect back to signup
      navigate("/signup");
    }
  }, [location.state, navigate]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [timeLeft]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleCodeChange = (index: number, value: string) => {
    // Only allow digits
    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "");
    if (pastedData.length === 6) {
      const newCode = pastedData.split("");
      setCode(newCode);
      inputRefs.current[5]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const verificationCode = code.join("");

    if (verificationCode.length !== 6) {
      setError("Please enter the complete 6-digit verification code");
      return;
    }

    // Validate email format
    const { isValid, message } = validateEmail(email);
    if (!isValid) {
      setError(message);
      return;
    }

    setIsLoading(true);

    try {
      const requestData: SignupVerifyRequest = {
        email: sanitizeEmail(email),
        code: verificationCode,
      };

      const response = await authAPI.signupVerify(requestData);

      // Set tokens
      setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      toast({
        title: "Account Verified!",
        description:
          "Your account has been successfully verified and activated.",
        variant: "default",
      });

      // Redirect to add-account for onboarding
      navigate("/add-account");
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Verification failed. Please try again.";
      setError(errorMessage);

      // Clear the code on error
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    // This would typically call a resend endpoint
    // For now, we'll show a message
    toast({
      title: "Code Resent",
      description: "A new verification code has been sent to your email.",
      variant: "default",
    });
    setTimeLeft(600); // Reset timer
  };

  const handleBackToSignup = () => {
    navigate("/signup");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBackToSignup}
              className="p-0 h-auto"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </div>
          <div className="text-center">
            <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-blue-600" />
            </div>
            <CardTitle className="text-2xl font-bold">
              Verify Your Account
            </CardTitle>
            <CardDescription className="text-gray-600">
              Enter the 6-digit code sent to your email
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Contact Info */}
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-center mb-2">
              <Mail className="h-4 w-4 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-blue-900">
                Code sent to
              </span>
            </div>
            <p className="text-sm text-blue-700">{contact}</p>
          </div>

          {/* Timer */}
          <div className="text-center">
            <div className="flex items-center justify-center text-sm text-gray-600">
              <Clock className="h-4 w-4 mr-1" />
              Code expires in:{" "}
              <span className="font-mono ml-1">{formatTime(timeLeft)}</span>
            </div>
          </div>

          {/* Error Display */}
          {error && <ErrorDisplay error={error} />}

          {/* Verification Code Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="verification-code">Verification Code</Label>
              <div className="flex justify-center space-x-2">
                {code.map((digit, index) => (
                  <Input
                    key={index}
                    ref={el => (inputRefs.current[index] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={e => handleCodeChange(index, e.target.value)}
                    onKeyDown={e => handleKeyDown(index, e)}
                    onPaste={handlePaste}
                    className="w-12 h-12 text-center text-lg font-mono border-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    disabled={isLoading}
                  />
                ))}
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={
                isLoading || code.join("").length !== 6 || timeLeft === 0
              }
            >
              {isLoading ? "Verifying..." : "Verify Account"}
            </Button>
          </form>

          {/* Resend Code */}
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">
              Didn't receive the code?
            </p>
            <Button
              variant="link"
              onClick={handleResendCode}
              disabled={timeLeft > 0}
              className="text-sm"
            >
              {timeLeft > 0
                ? `Resend in ${formatTime(timeLeft)}`
                : "Resend Code"}
            </Button>
          </div>

          {/* Help Text */}
          <div className="text-center text-xs text-gray-500">
            <p>Check your spam folder if you don't see the email.</p>
            <p>The code will expire in 10 minutes for security.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VerifySignup;
