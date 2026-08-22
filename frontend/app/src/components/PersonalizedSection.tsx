import avatarUser from "@/assets/avatar-user.jpg";

const PersonalizedSection = () => {
  return (
    <section className="py-24 sm:py-32" id="personalized">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="perspective-container">
            <div className="relative perspective-card">
              <div className="bg-background/50 rounded-2xl p-8 border border-border shadow-2xl shadow-muted/50">
                <div className="flex items-center mb-4">
                  <img
                    alt="User avatar"
                    className="w-12 h-12 rounded-full mr-4 border-2 border-primary"
                    src={avatarUser}
                  />
                  <div>
                    <p className="font-bold text-foreground text-lg">
                      Your Personalized Feed
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Curated by your AI assistant
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="font-semibold text-primary text-sm">
                      Priority Alert
                    </p>
                    <p className="text-foreground">
                      Email from 'Innovate Corp' requires immediate attention.
                    </p>
                  </div>
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="font-semibold text-success text-sm">
                      Draft Suggestion
                    </p>
                    <p className="text-foreground">
                      AI has drafted a follow-up to your meeting with Michael
                      Chen.
                    </p>
                  </div>
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="font-semibold text-warning text-sm">
                      Weekly Summary
                    </p>
                    <p className="text-foreground">
                      You've saved an estimated 4.5 hours this week using
                      Axnore.
                    </p>
                  </div>
                </div>
              </div>

              {/* Floating elements */}
              <div className="absolute -top-8 -right-8 w-24 h-24 bg-primary/40 rounded-full blur-3xl floating-element opacity-50" />
              <div
                className="absolute -bottom-8 -left-8 w-24 h-24 bg-warning/40 rounded-full blur-3xl floating-element opacity-50"
                style={{ animationDelay: "-3s" }}
              />
            </div>
          </div>

          <div className="text-center lg:text-left">
            <h2 className="text-4xl sm:text-5xl font-bold text-foreground">
              Built Around <span className="text-primary">You</span>. Literally.
            </h2>
            <p className="mt-6 text-lg text-muted-foreground">
              Axnore's AI doesn't just work for you; it learns from you. It
              studies your workflow, understands your priorities, and
              anticipates your needs to create a truly personalized and
              proactive email environment. Your workspace evolves as you do.
            </p>
            <a
              href="#"
              className="mt-8 inline-flex items-center group bg-transparent border-2 border-primary text-primary px-8 py-3 rounded-lg font-semibold text-lg transition-all duration-300 hover:bg-primary hover:text-primary-foreground hover:shadow-lg hover:shadow-primary/30"
            >
              Customize Your AI
              <svg
                className="ml-2 w-5 h-5 transition-transform duration-300 group-hover:translate-x-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PersonalizedSection;
