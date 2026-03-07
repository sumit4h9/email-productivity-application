const Footer = () => {
  const footerSections = [
    {
      title: "Product",
      links: ["Features", "Security", "Pricing", "Integrations"],
    },
    {
      title: "Company",
      links: ["About Us", "Careers", "Press"],
    },
    {
      title: "Resources",
      links: ["Blog", "Help Center", "API Docs"],
    },
    {
      title: "Legal",
      links: ["Privacy", "Terms"],
    },
  ];

  return (
    <footer className="bg-muted/50 text-foreground">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
          <div className="col-span-2 lg:col-span-1">
            <a href="#" className="flex items-center space-x-2">
              <div className="w-8 h-8 flex items-center justify-center">
                <svg
                  className="w-full h-full text-primary"
                  fill="none"
                  height="32"
                  viewBox="0 0 40 40"
                  width="32"
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
              <span className="text-2xl font-bold text-foreground">Axnore</span>
            </a>
            <p className="mt-4 text-muted-foreground">
              Engineering the future of intelligent communication.
            </p>
          </div>

          {footerSections.map((section, index) => (
            <div key={index}>
              <h4 className="font-semibold text-foreground">{section.title}</h4>
              <ul className="mt-4 space-y-3">
                {section.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <a
                      href="#"
                      className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-16 border-t border-border pt-8 flex flex-col sm:flex-row justify-between items-center">
          <p className="text-muted-foreground">
            © 2025 Axnore. All rights reserved.
          </p>
          <div className="flex space-x-6 mt-4 sm:mt-0">
            <a
              href="#"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.71v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
              </svg>
            </a>
            <a
              href="#"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  clipRule="evenodd"
                  d="M12 2C6.477 2 2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12c0-5.523-4.477-10-10-10z"
                  fillRule="evenodd"
                />
              </svg>
            </a>
            <a
              href="#"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M16.6 5.9c.7 0 1.2.5 1.2 1.2s-.5 1.2-1.2 1.2-1.2-.5-1.2-1.2.5-1.2 1.2-1.2zm-4.6 2.5c-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4-1.8-4-4-4zm0 6.5c-1.4 0-2.5-1.1-2.5-2.5s1.1-2.5 2.5-2.5 2.5 1.1 2.5 2.5-1.1 2.5-2.5 2.5zM12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm6 12.9c0 .8-.1 1.5-.3 2.2-.3.9-.8 1.6-1.5 2.3s-1.4.9-2.3 1.2c-.7.2-1.4.3-2.2.3s-1.5-.1-2.2-.3c-.9-.3-1.6-.8-2.3-1.5s-.9-1.4-1.2-2.3c-.2-.7-.3-1.4-.3-2.2v-1.8c0-.8.1-1.5.3-2.2.3-.9.8-1.6 1.5-2.3s1.4-.9 2.3-1.2c.7-.2 1.4-.3 2.2-.3s1.5.1 2.2.3c.9.3 1.6.8 2.3 1.5s.9 1.4 1.2 2.3c.2.7.3 1.4.3 2.2v1.8z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
