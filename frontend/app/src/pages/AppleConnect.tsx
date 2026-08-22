/** @jsxImportSource react */
import React, { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

const AppleConnect = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [appleId, setAppleId] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const isAppleEmail = (email: string) =>
    /@(?:icloud\.com|me\.com|mac\.com)$/i.test(email.trim());

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      if (!isAppleEmail(appleId)) {
        throw new Error(
          "Please use an Apple Mail address (icloud.com, me.com, or mac.com)"
        );
      }
      // TODO: Replace with backend call that performs secure IMAP/SMTP validation
      await new Promise(res => setTimeout(res, 1200));

      toast({
        title: "Apple account connected",
        description: "We will fetch mail metadata via IMAP/SMTP shortly.",
      });
      navigate("/dashboard");
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Please verify your credentials and try again.";
      toast({
        title: "Connection failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md bg-card border border-border rounded-xl shadow-sm p-6">
        <div className="text-center mb-6">
          <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-3">
            <span className="material-icons text-2xl">apple</span>
          </div>
          <h1 className="text-2xl font-semibold">Connect Apple ID</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Enter your Apple ID credentials to sync via IMAP/SMTP.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Apple ID (email)
            </label>
            <input
              type="email"
              required
              value={appleId}
              onChange={e => setAppleId(e.target.value)}
              className="w-full px-3 py-2 border border-input rounded-md bg-background"
              placeholder="name@icloud.com"
              pattern="^[^@\s]+@(icloud\.com|me\.com|mac\.com)$"
              title="Only Apple Mail addresses are allowed: icloud.com, me.com, mac.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-input rounded-md bg-background"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-2 rounded-md text-white ${isLoading ? "bg-gray-400" : "bg-gray-900 hover:bg-gray-800"}`}
          >
            {isLoading ? "Connecting…" : "Connect Apple Account"}
          </button>

          <p className="text-xs text-muted-foreground mt-2">
            Note: For two-factor accounts, create an app-specific password in
            your Apple ID settings.
          </p>
        </form>
      </div>
    </div>
  );
};

export default AppleConnect;
