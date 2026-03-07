import { Button } from "@/components/ui/button";

const CTASection = () => {
  return (
    <section className="bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32 text-center">
        <div className="relative bg-gradient-to-br from-primary to-primary-light rounded-3xl p-10 sm:p-16 overflow-hidden">
          {/* Background effects */}
          <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.1] z-0" />
          <div className="absolute -top-1/2 -left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-[spin_20s_linear_infinite] z-0" />

          <div className="relative z-10">
            <h2 className="text-4xl sm:text-5xl font-bold text-primary-foreground">
              Redefine Your Reality.
            </h2>
            <p className="mt-4 text-lg text-primary-foreground/90 max-w-2xl mx-auto">
              Step into the future of communication. It's time to stop managing
              email and start commanding it.
            </p>
            <div className="mt-10">
              <Button className="inline-flex items-center group bg-background text-primary px-10 py-4 rounded-xl font-bold text-lg shadow-2xl hover:bg-muted transition-all transform hover:scale-105">
                Claim Your Future Free
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
