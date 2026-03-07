import React from "react";

interface LogoProps {
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ className = "w-7 h-7" }) => {
  const msBlue = "#00A4EF";
  return <img src="/logo.svg" alt="Logo" className={className} />;
};

export default Logo;
