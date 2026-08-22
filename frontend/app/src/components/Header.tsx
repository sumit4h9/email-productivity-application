import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Header = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${
        isScrolled ? "bg-background/80 backdrop-blur-xl shadow-lg" : ""
      }`}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-24">
          {/* LOGO */}
          <div className="flex items-center">
            <a href="#" className="flex items-center space-x-3">
              <div className="w-10 h-10 flex items-center justify-center logo-animate">
                {/* Prefer image if available, fallback to SVG */}
                <img
                  src="/lovable-uploads/bb479371-9a2c-43a1-b281-4e5dcaacbce4.png"
                  alt="Axnore Logo"
                  className="w-full h-full object-contain hidden dark:block"
                  onError={e => {
                    (e.currentTarget as HTMLImageElement).style.display =
                      "none";
                  }}
                />
                <svg
                  className="w-full h-full text-primary"
                  fill="none"
                  height="40"
                  viewBox="0 0 40 40"
                  width="40"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M20 38C30.4934 38 39 29.4934 39 19C39 8.50659 30.4934 0 20 0C9.50659 0 1 8.50659 1 19C1 29.4934 9.50659 38 20 38Z"
                    stroke="currentColor"
                    strokeOpacity="0.3"
                    strokeWidth="2"
                  />
                  <path
                    d="M11.6667 19.9998L17.5 14.1665L23.3333 19.9998L29.1667 14.1665"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="3"
                  />
                  <path
                    d="M11.6667 25.8332L17.5 19.9998L23.3333 25.8332L29.1667 19.9998"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="3"
                  />
                </svg>
              </div>
              <span className="text-3xl font-bold text-foreground tracking-wider">
                Axnore
              </span>
            </a>
          </div>

          {/* NAVIGATION */}
          <nav className="hidden lg:flex items-center space-x-10">
            <button
              onClick={() => scrollToSection("features")}
              className="text-muted-foreground hover:text-foreground font-medium nav-link"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection("personalized")}
              className="text-muted-foreground hover:text-foreground font-medium nav-link"
            >
              Your AI
            </button>
            <button
              onClick={() => scrollToSection("testimonials")}
              className="text-muted-foreground hover:text-foreground font-medium nav-link"
            >
              Testimonials
            </button>
          </nav>

          {/* AUTH BUTTONS */}
          <div className="flex items-center space-x-4">
            <Link
              to="/login"
              className="text-muted-foreground hover:text-foreground font-medium transition-colors hidden sm:block"
            >
              Log In
            </Link>
            <Link to="/signup">
              <Button className="bg-primary text-primary-foreground px-6 py-3 font-semibold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all duration-300 transform hover:scale-105">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
