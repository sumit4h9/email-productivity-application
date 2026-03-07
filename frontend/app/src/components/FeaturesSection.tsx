const FeaturesSection = () => {
  const features = [
    {
      title: "Cognitive Shield",
      description:
        "Our self-learning AI anticipates and neutralizes threats before they even exist, protecting your digital identity with predictive intelligence.",
      color: "primary",
      glowColor: "rgba(99, 102, 241, 0.3)",
      icon: (
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          />
        </svg>
      ),
    },
    {
      title: "AI Flow Composer",
      description:
        "Go beyond drafts. Our AI builds entire email sequences and workflows based on your goals, automating your communication strategy.",
      color: "success",
      glowColor: "rgba(16, 185, 129, 0.3)",
      icon: (
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
      ),
    },
    {
      title: "Adaptive Inbox",
      description:
        "Your inbox reconfigures itself in real-time based on your current task, focus, and priorities. The right email, at the right time. Always.",
      color: "warning",
      glowColor: "rgba(168, 85, 247, 0.3)",
      icon: (
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
    },
  ];

  const getColorClasses = (color: string) => {
    switch (color) {
      case "primary":
        return "bg-primary/10 text-primary border-primary/20";
      case "success":
        return "bg-success/10 text-success border-success/20";
      case "warning":
        return "bg-warning/10 text-warning border-warning/20";
      default:
        return "bg-primary/10 text-primary border-primary/20";
    }
  };

  return (
    <section className="py-24 sm:py-32 bg-muted/30" id="features">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-20">
          <h2 className="text-4xl sm:text-5xl font-bold text-foreground">
            A New Dimension of Email
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            Features so advanced, they feel like the future.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-12">
          {features.map((feature, index) => (
            <div key={index} className="feature-card p-8 rounded-2xl">
              <div
                className={`flex items-center justify-center h-16 w-16 rounded-full mb-6 border glow-pulse ${getColorClasses(feature.color)}`}
                style={
                  { "--glow-color": feature.glowColor } as React.CSSProperties
                }
              >
                {feature.icon}
              </div>
              <h3 className="text-2xl font-semibold text-foreground mb-4">
                {feature.title}
              </h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
