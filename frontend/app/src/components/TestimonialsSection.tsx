import avatarSarah from "@/assets/avatar-sarah.jpg";
import avatarMichael from "@/assets/avatar-michael.jpg";
import avatarEmily from "@/assets/avatar-emily.jpg";

const TestimonialsSection = () => {
  const testimonials = [
    {
      quote:
        "Axnore isn't an email client, it's a command center. The predictive security has given our entire organization peace of mind we never thought possible.",
      name: "Sarah Jones",
      title: "CTO, Innovate Corp",
      avatar: avatarSarah,
    },
    {
      quote:
        "The AI Flow Composer is pure genius. It automated a client onboarding sequence that used to take me hours per week. I'm not just saving time, I'm scaling my business.",
      name: "Michael Chen",
      title: "Founder, Nexus Dynamics",
      avatar: avatarMichael,
      featured: true,
    },
    {
      quote:
        "I was skeptical about the 'Adaptive Inbox', but it's magical. It's like my inbox knows what I need to focus on before I do. My productivity and focus have skyrocketed.",
      name: "Emily Rodriguez",
      title: "Lead Digital Strategist",
      avatar: avatarEmily,
    },
  ];

  return (
    <section className="py-24 sm:py-32 bg-muted/30" id="testimonials">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-20">
          <h2 className="text-4xl sm:text-5xl font-bold text-foreground">
            Echoes from the Future
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            Hear from pioneers who've already made the leap.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className={`feature-card p-8 rounded-2xl flex flex-col ${
                testimonial.featured
                  ? "md:scale-105 md:border-primary/80 bg-background"
                  : ""
              }`}
            >
              <p className="text-muted-foreground mb-6 flex-grow">
                "{testimonial.quote}"
              </p>
              <div className="flex items-center mt-auto">
                <img
                  alt={`${testimonial.name} avatar`}
                  className="w-12 h-12 rounded-full mr-4 border-2 border-border"
                  src={testimonial.avatar}
                />
                <div>
                  <p className="font-semibold text-foreground">
                    {testimonial.name}
                  </p>
                  <p className="text-muted-foreground text-sm">
                    {testimonial.title}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;
