import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ErrorDisplay } from "@/components/ui/error-display";
import { useToast } from "@/hooks/use-toast";
import { Eye, EyeOff } from "lucide-react";
import { sanitizeEmail, sanitizePassword } from "@/lib/security";
import { validateUsername, validateEmail } from "@/lib/validation";
import { authAPI, SignupInitRequest } from "@/lib/api";

const Signup = () => {
  const [username, setUsername] = useState("");
  const [usernameError, setUsernameError] = useState("");
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Password validation state
  const [passwordValidation, setPasswordValidation] = useState({
    isValid: false,
    suggestions: [] as string[],
  });

  const { toast } = useToast();
  const navigate = useNavigate();

  // Password strength & validation logic
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

  const validatePassword = (password: string) => {
    const suggestions: string[] = [];
    if (password.length < 8) suggestions.push("At least 8 characters");
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSymbol = /[@!#$%^*]/.test(password);

    // Require specific character types
    if (!hasUpper) suggestions.push("At least one uppercase letter");
    if (!hasLower) suggestions.push("At least one lowercase letter");
    if (!hasNumber) suggestions.push("At least one number");
    if (!hasSymbol) suggestions.push("At least one symbol (@!#$%^*)");

    setPasswordValidation({
      isValid: suggestions.length === 0,
      suggestions,
    });
  };

  const passwordStrength = getPasswordStrength(password);
  const strengthLabels = [
    "Very Weak",
    "Weak",
    "Fair",
    "Good",
    "Strong",
    "Excellent",
  ];
  const strengthColors = [
    "bg-red-500",
    "bg-red-400",
    "bg-yellow-500",
    "bg-blue-500",
    "bg-green-500",
  ];

  useEffect(() => {
    validatePassword(password);
  }, [password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password || !username) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    const { isValid: isEmailValid, message: emailMsg } = validateEmail(email);
    if (!isEmailValid) {
      setEmailError(emailMsg);
      toast({
        title: "Validation Error",
        description: emailMsg,
        variant: "destructive",
      });
      return;
    }

    if (password !== confirmPassword) {
      toast({
        title: "Validation Error",
        description: "Passwords do not match.",
        variant: "destructive",
      });
      return;
    }

    if (!passwordValidation.isValid) {
      setError("Please fix password issues before submitting.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    // Validate username
    const usernameValidation = validateUsername(username);
    if (!usernameValidation.isValid) {
      setError(usernameValidation.message);
      return;
    }

    try {
      sanitizeEmail(email);
      sanitizePassword(password);
    } catch (securityError) {
      const errorMessage =
        securityError instanceof Error
          ? securityError.message
          : "Security validation failed";
      setError(`Security validation failed: ${errorMessage}`);
      toast({
        title: "Security Validation Failed",
        description: errorMessage,
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const payload: SignupInitRequest = {
        email: sanitizeEmail(email),
        password: sanitizePassword(password),
        username: username.toLowerCase(),
      };

      const response = await authAPI.signupInit(payload);

      // Show success message
      toast({
        title: "Verification Code Sent!",
        description: response.message,
        variant: "default",
      });

      // Navigate to verification page with state
      navigate("/verify-signup", {
        state: {
          email: sanitizeEmail(email),
          contact: response.contact,
          message: response.message,
        },
      });
    } catch (err: unknown) {
      console.error("Signup init error:", err);
      if (err && typeof err === "object" && "response" in err) {
        const response = (
          err as { response?: { status?: number; data?: { detail?: unknown } } }
        ).response;
        if (response?.status === 422) {
          const detail = response.data?.detail;
          if (Array.isArray(detail)) {
            const errorMessages = detail
              .map(
                (error: { loc?: string[]; msg?: string }) =>
                  `${error.loc?.join(".") || "unknown"}: ${error.msg || "Unknown error"}`
              )
              .join(", ");
            setError(`Validation error: ${errorMessages}`);
          } else if (typeof detail === "string") {
            setError(detail);
          } else {
            setError("Please check your input and try again.");
          }
        } else if (response?.status === 400) {
          setError(
            typeof response.data?.detail === "string"
              ? response.data.detail
              : "Invalid request data"
          );
        } else {
          setError(
            typeof response?.data?.detail === "string"
              ? response.data.detail
              : "Signup failed. Please try again."
          );
        }
      } else {
        setError("Signup failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* LEFT SIDE */}
      <div className="flex flex-1 flex-col justify-center py-3 px-4 sm:px-6 lg:flex-none lg:px-12 xl:px-16">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div>
            <div className="flex items-center mb-2">
              <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center mr-2">
                <span className="material-icons text-white text-xl">
                  all_inclusive
                </span>
              </div>
              <h1 className="text-xl font-extrabold text-gray-900">Axnore</h1>
            </div>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tighter text-gray-900">
              Create account
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Start your journey with us today.
            </p>
          </div>

          {/* Removed social signup buttons */}

          {/* Signup Form */}
          <form className="mt-3 space-y-3" onSubmit={handleSubmit}>
            <div>
              <Label htmlFor="username" className="text-sm block mb-1.5">
                Username
              </Label>
              <div className="text-xs text-muted-foreground mb-1.5">
                (5-20 characters, letters, numbers, ., _, -)
              </div>
              <Input
                id="username"
                type="text"
                required
                placeholder="e.g., john.doe123"
                value={username}
                onChange={e => {
                  const value = e.target.value.toLowerCase();
                  setUsername(value);
                  const validation = validateUsername(value);
                  setUsernameError(validation.message);
                }}
                className={`py-1.5 text-sm ${usernameError ? "border-red-500 focus-visible:ring-red-500" : ""}`}
                aria-describedby="username-error"
              />
              {usernameError && (
                <p className="mt-1 text-xs text-red-500" id="username-error">
                  {usernameError}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="email" className="text-sm block mb-1.5">
                Email address
              </Label>
              {/* <div className="text-xs text-muted-foreground mb-1.5">
                (Use email from: gmail, yahoo, outlook, hotmail, icloud, apple, or microsoft)
              </div> */}
              <Input
                id="email"
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={e => {
                  setEmail(e.target.value);
                  const { isValid, message } = validateEmail(e.target.value);
                  setEmailError(isValid ? "" : message);
                }}
                className={`py-1.5 text-sm ${emailError ? "border-red-500 focus-visible:ring-red-500" : ""}`}
                aria-describedby="signup-email-error"
              />
              {emailError && (
                <p
                  className="mt-1 text-xs text-red-500"
                  id="signup-email-error"
                >
                  {emailError}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="password" className="text-sm">
                Password
              </Label>
              <div className="relative mt-1">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="pr-10 py-1.5 text-sm"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <Eye className="h-5 w-5 text-muted-foreground" />
                  )}
                </button>
              </div>
              {password && (
                <div className="mt-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span>Password strength:</span>
                    <span
                      className={`font-medium ${
                        passwordStrength === 0
                          ? "text-red-500"
                          : passwordStrength === 1
                            ? "text-red-500"
                            : passwordStrength === 2
                              ? "text-yellow-500"
                              : passwordStrength === 3
                                ? "text-blue-500"
                                : "text-green-500"
                      }`}
                    >
                      {passwordStrength === 0
                        ? "Very Weak"
                        : strengthLabels[passwordStrength] || "Very Weak"}
                    </span>
                  </div>
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5].map(level => (
                      <div
                        key={level}
                        className={`h-2 flex-1 rounded-full ${
                          level <= passwordStrength
                            ? strengthColors[Math.min(passwordStrength, 4)]
                            : "bg-muted"
                        }`}
                      />
                    ))}
                  </div>
                  {passwordValidation.suggestions.length > 0 && (
                    <ul className="text-xs mt-1 text-red-500 list-disc ml-4">
                      {passwordValidation.suggestions.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
            <div>
              <Label htmlFor="confirm-password" className="text-sm">
                Confirm password
              </Label>
              <div className="relative mt-1">
                <Input
                  id="confirm-password"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  placeholder="•••••••••"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  className="pr-10 py-1.5 text-sm"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <Eye className="h-5 w-5 text-muted-foreground" />
                  )}
                </button>
              </div>
            </div>

            {/* Error message */}
            <ErrorDisplay error={error} />

            <div>
              <button
                type="submit"
                disabled={
                  isLoading ||
                  !passwordValidation.isValid ||
                  password.length < 8
                }
                className="flex w-full justify-center rounded-lg bg-gray-900 py-2 px-4 text-sm font-semibold text-white shadow-sm hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                {isLoading ? "Creating account..." : "Sign up"}
              </button>
            </div>
          </form>

          <p className="mt-3 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold text-primary hover:text-primary/80"
            >
              Log in
            </Link>
          </p>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div className="relative hidden w-0 flex-1 lg:block signup-pattern-bg overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/30 via-slate-900/50 to-purple-900/30"></div>
        <div className="globe-container">
          <div className="globe">
            <div className="globe-ring globe-ring-1"></div>
            <div className="globe-ring globe-ring-2"></div>
            <div className="globe-ring globe-ring-3"></div>
            <div className="globe-ring globe-ring-4"></div>
            <div className="globe-ring globe-ring-5"></div>
            <div className="globe-ring globe-ring-6"></div>
            <div
              className="data-point"
              style={{ top: "25%", left: "75%", animationDelay: "-0.2s" }}
            ></div>
            <div
              className="data-point"
              style={{
                top: "80%",
                left: "85%",
                animationDelay: "-0.8s",
                backgroundColor: "#f472b6",
              }}
            ></div>
            <div
              className="data-point"
              style={{ top: "50%", left: "10%", animationDelay: "-1.5s" }}
            ></div>
            <div
              className="data-point"
              style={{
                top: "15%",
                left: "30%",
                animationDelay: "-2s",
                backgroundColor: "#60a5fa",
              }}
            ></div>
            <div
              className="data-point"
              style={{ top: "65%", left: "45%", animationDelay: "-0.5s" }}
            ></div>
            <div
              className="data-point"
              style={{
                top: "90%",
                left: "60%",
                animationDelay: "-1.2s",
                backgroundColor: "#f472b6",
              }}
            ></div>
            <div
              className="data-point"
              style={{
                top: "30%",
                left: "5%",
                animationDelay: "-1.8s",
                backgroundColor: "#60a5fa",
              }}
            ></div>
          </div>
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-center p-8 relative z-10">
            <h2 className="text-4xl font-black tracking-tighter mb-3 text-shadow">
              Unlock the Future of Email
            </h2>
            <p className="text-lg text-slate-200 max-w-md mx-auto text-shadow">
              Harnessing AI to revolutionize your inbox. Experience unparalleled
              efficiency and intelligence.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;
