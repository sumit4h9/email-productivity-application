"use client";
import React, { useEffect } from "react";
import * as THREE from "three";

type CSSPropertiesWithVars = React.CSSProperties &
  Record<string, string | number>;

export default function Page() {
  useEffect(() => {
    const canvas = document.getElementById(
      "hero-canvas"
    ) as HTMLCanvasElement | null;
    if (!canvas) return;

    let scene: THREE.Scene;
    let camera: THREE.PerspectiveCamera;
    let renderer: THREE.WebGLRenderer;
    let mesh: THREE.Mesh;
    let mouseX = 0;
    let mouseY = 0;

    function init() {
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
      );
      camera.position.z = 2.5;

      renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      const geometry = new THREE.IcosahedronGeometry(1.5, 30);
      const material = new THREE.ShaderMaterial({
        uniforms: {
          uTime: { value: 0 },
          uColor1: { value: new THREE.Color(0x6366f1) },
          uColor2: { value: new THREE.Color(0x818cf8) },
          uColor3: { value: new THREE.Color(0xa5b4fc) },
        },
        vertexShader: `
          uniform float uTime;
          varying vec3 vPosition;
          varying vec3 vNormal;
          void main() {
            vPosition = position;
            vNormal = normal;
            float displacement = sin(position.x * 4.0 + uTime * 0.5) * 0.1 +
                                 sin(position.y * 4.0 + uTime * 0.3) * 0.1 +
                                 sin(position.z * 4.0 + uTime * 0.2) * 0.1;
            vec3 newPosition = position + normal * displacement;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
          }
        `,
        fragmentShader: `
          uniform float uTime;
          uniform vec3 uColor1;
          uniform vec3 uColor2;
          uniform vec3 uColor3;
          varying vec3 vPosition;
          varying vec3 vNormal;
          void main() {
            float intensity = pow(0.7 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
            vec3 colorMix1 = mix(uColor1, uColor2, sin(uTime * 0.5) * 0.5 + 0.5);
            vec3 colorMix2 = mix(colorMix1, uColor3, cos(vPosition.y * 2.0 + uTime * 0.3) * 0.5 + 0.5);
            vec3 finalColor = colorMix2 * intensity;
            gl_FragColor = vec4(finalColor, intensity * 0.5);
          }
        `,
        wireframe: true,
        transparent: true,
        blending: THREE.AdditiveBlending,
      });
      mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      window.addEventListener("resize", onWindowResize);
      document.addEventListener("mousemove", onMouseMove);
      animate();
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function onMouseMove(event: MouseEvent) {
      mouseX = (event.clientX - window.innerWidth / 2) * 0.0005;
      mouseY = (event.clientY - window.innerHeight / 2) * 0.0005;
    }

    const clock = new THREE.Clock();
    function animate() {
      requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();
      (mesh.material as THREE.ShaderMaterial).uniforms.uTime.value =
        elapsedTime;
      mesh.rotation.y = elapsedTime * 0.05;
      mesh.rotation.x = elapsedTime * 0.05;
      camera.position.x += (mouseX - camera.position.x) * 0.05;
      camera.position.y += (-mouseY - camera.position.y) * 0.05;
      camera.lookAt(scene.position);
      renderer.render(scene, camera);
    }

    init();

    const navbar = document.getElementById("navbar");
    const onScroll = () => {
      if (!navbar) return;
      if (window.scrollY > 50) {
        navbar.classList.add("bg-white/80", "backdrop-blur-xl", "shadow-lg");
      } else {
        navbar.classList.remove("bg-white/80", "backdrop-blur-xl", "shadow-lg");
      }
    };
    window.addEventListener("scroll", onScroll);

    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onWindowResize);
      document.removeEventListener("mousemove", onMouseMove);
      renderer?.dispose();
    };
  }, []);

  return (
    <div className="text-gray-800">
      {/* --- HEADER --- */}
      <header
        id="navbar"
        className="fixed top-0 left-0 w-full z-50 transition-all duration-300 bg-white/70 backdrop-blur-md shadow-sm"
      >
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            {/* Logo */}
            <a href="#" className="flex items-center space-x-3">
              <div className="w-10 h-10 flex items-center justify-center logo-animate">
                {/* svg logo */}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="40"
                  height="40"
                  viewBox="0 0 40 40"
                  className="w-full h-full text-indigo-500"
                  fill="none"
                >
                  <path
                    d="M20 38C30.4934 38 39 29.4934 39 19C39 8.50659 30.4934 0 20 0C9.50659 0 1 8.50659 1 19C1 29.4934 9.50659 38 20 38Z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeOpacity="0.3"
                  />
                  <path
                    d="M11.6667 19.9998L17.5 14.1665L23.3333 19.9998L29.1667 14.1665"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M11.6667 25.8332L17.5 19.9998L23.3333 25.8332L29.1667 19.9998"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span className="text-3xl font-bold text-gray-900 tracking-wider">
                Axnore
              </span>
            </a>

            {/* Nav */}
            <nav className="hidden lg:flex items-center space-x-10">
              <a
                href="#features"
                className="nav-link font-medium text-gray-600 hover:text-gray-900"
              >
                Features
              </a>
              <a
                href="#personalized"
                className="nav-link font-medium text-gray-600 hover:text-gray-900"
              >
                Your AI
              </a>
              <a
                href="#testimonials"
                className="nav-link font-medium text-gray-600 hover:text-gray-900"
              >
                Testimonials
              </a>
            </nav>

            {/* CTA */}
            <div className="flex items-center space-x-4">
              <a
                href="#"
                className="hidden sm:block font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Log In
              </a>
              <a
                href="#"
                className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold shadow-lg shadow-indigo-500/20 hover:bg-indigo-700 transition-all duration-300 transform hover:scale-105"
              >
                Get Started
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* --- HERO --- */}
      <main>
        <section className="relative hero-gradient text-gray-900 min-h-screen flex items-center justify-center overflow-hidden">
          <canvas id="hero-canvas"></canvas>
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center pt-24 sm:pt-32">
            <div className="animate-fadeInDown">
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-tight bg-clip-text text-transparent bg-gradient-to-br from-gray-900 to-gray-600">
                Beyond Inbox.
              </h1>
              <h2 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-tight bg-clip-text text-transparent bg-gradient-to-br from-indigo-500 to-indigo-700 mt-2">
                Enter Axnore.
              </h2>
            </div>
            <p className="mt-8 max-w-3xl mx-auto text-lg sm:text-xl text-gray-600 animate-fadeInDown delay-200">
              An intelligent email experience that adapts to you. Powered by
              next-generation AI to deliver unparalleled productivity, security,
              and a touch of magic.
            </p>
            <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6 animate-fadeInDown delay-400">
              <a
                href="#"
                className="w-full sm:w-auto bg-indigo-600 text-white px-10 py-4 rounded-xl font-bold text-lg shadow-2xl shadow-indigo-600/30 transition-all transform hover:scale-105 hover:shadow-indigo-500/50"
              >
                Experience the Future
              </a>
              <a
                href="#"
                className="w-full sm:w-auto border-2 border-gray-300 text-gray-700 px-10 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 hover:border-gray-400 transition-colors"
              >
                Watch Demo
              </a>
            </div>
          </div>
        </section>

        <section id="features" className="py-24 sm:py-32 bg-gray-50">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-20">
              <h2 className="text-4xl sm:text-5xl font-bold text-gray-900">
                A New Dimension of Email
              </h2>
              <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
                Features so advanced, they feel like the future.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-12">
              <div className="feature-card p-8 rounded-2xl">
                <div
                  className="flex items-center justify-center h-16 w-16 rounded-full bg-indigo-500/10 text-indigo-500 mb-6 border border-indigo-500/20 glow-pulse"
                  style={
                    {
                      "--glow-color": "rgba(99, 102, 241, 0.3)",
                    } as CSSPropertiesWithVars
                  }
                >
                  <span className="material-symbols-outlined text-4xl">
                    neurology
                  </span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                  Cognitive Shield
                </h3>
                <p className="text-gray-600">
                  Our self-learning AI anticipates and neutralizes threats
                  before they even exist, protecting your digital identity with
                  predictive intelligence.
                </p>
              </div>
              <div className="feature-card p-8 rounded-2xl">
                <div
                  className="flex items-center justify-center h-16 w-16 rounded-full bg-green-500/10 text-green-500 mb-6 border border-green-500/20 glow-pulse"
                  style={
                    {
                      "--glow-color": "rgba(16, 185, 129, 0.3)",
                    } as CSSPropertiesWithVars
                  }
                >
                  <span className="material-symbols-outlined text-4xl">
                    dynamic_form
                  </span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                  AI Flow Composer
                </h3>
                <p className="text-gray-600">
                  Go beyond drafts. Our AI builds entire email sequences and
                  workflows based on your goals, automating your communication
                  strategy.
                </p>
              </div>
              <div className="feature-card p-8 rounded-2xl">
                <div
                  className="flex items-center justify-center h-16 w-16 rounded-full bg-purple-500/10 text-purple-500 mb-6 border border-purple-500/20 glow-pulse"
                  style={
                    {
                      "--glow-color": "rgba(168, 85, 247, 0.3)",
                    } as CSSPropertiesWithVars
                  }
                >
                  <span className="material-symbols-outlined text-4xl">
                    hub
                  </span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                  Adaptive Inbox
                </h3>
                <p className="text-gray-600">
                  Your inbox reconfigures itself in real-time based on your
                  current task, focus, and priorities. The right email, at the
                  right time. Always.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="personalized" className="py-24 sm:py-32">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div className="perspective-container">
                <div className="relative perspective-card">
                  <div className="bg-white/50 rounded-2xl p-8 border border-gray-200 shadow-2xl shadow-gray-200/50">
                    <div className="flex items-center mb-4">
                      <img
                        alt="User avatar"
                        className="w-12 h-12 rounded-full mr-4 border-2 border-indigo-500"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuAzG5zOfLW03PTYpqkybnAI5NnRdFgxOiu1x6FxRwT3Uut_Mz-pQrzU5cxmcZBE0MW-gre-qbenJdIbaO7V73gQCiFrnh7XcxNN3DQlk_hWhz-7ItjtdcU7a_ZRPSj8G_ppdWgYkc_YzSwY8FARNoXMaXE4XXBceoZkvpNDu1jitBZd5VoCQEi-Jzs5ugAGSE1NDVr8L0bd5LWPBJZSO9q4EDnEoez0OC370oe8Lm3M1n2iuZSd5X2-N3_SDZ7OmBDz5ZUDnBZxTdfi"
                      />
                      <div>
                        <p className="font-bold text-gray-900 text-lg">
                          Your Personalized Feed
                        </p>
                        <p className="text-sm text-gray-600">
                          Curated by your AI assistant
                        </p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="bg-gray-100 p-4 rounded-lg">
                        <p className="font-semibold text-indigo-600 text-sm">
                          Priority Alert
                        </p>
                        <p className="text-gray-800">
                          Email from 'Innovate Corp' requires immediate
                          attention.
                        </p>
                      </div>
                      <div className="bg-gray-100 p-4 rounded-lg">
                        <p className="font-semibold text-green-600 text-sm">
                          Draft Suggestion
                        </p>
                        <p className="text-gray-800">
                          AI has drafted a follow-up to your meeting with
                          Michael Chen.
                        </p>
                      </div>
                      <div className="bg-gray-100 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-600 text-sm">
                          Weekly Summary
                        </p>
                        <p className="text-gray-800">
                          You've saved an estimated 4.5 hours this week using
                          Axnore.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="absolute -top-8 -right-8 w-24 h-24 bg-indigo-400 rounded-full blur-3xl floating-element opacity-50"></div>
                  <div
                    className="absolute -bottom-8 -left-8 w-24 h-24 bg-purple-400 rounded-full blur-3xl floating-element opacity-50"
                    style={{ animationDelay: "-3s" }}
                  ></div>
                </div>
              </div>
              <div className="text-center lg:text-left">
                <h2 className="text-4xl sm:text-5xl font-bold text-gray-900">
                  Built Around <span className="text-indigo-600">You</span>.
                  Literally.
                </h2>
                <p className="mt-6 text-lg text-gray-600">
                  Axnore's AI doesn't just work for you; it learns from you. It
                  studies your workflow, understands your priorities, and
                  anticipates your needs to create a truly personalized and
                  proactive email environment. Your workspace evolves as you do.
                </p>
                <a
                  className="mt-8 inline-flex items-center group bg-transparent border-2 border-indigo-600 text-indigo-600 px-8 py-3 rounded-lg font-semibold text-lg transition-all duration-300 hover:bg-indigo-600 hover:text-white hover:shadow-lg hover:shadow-indigo-500/30"
                  href="#"
                >
                  Customize Your AI
                  <span className="material-symbols-outlined ml-2 transition-transform duration-300 group-hover:translate-x-1">
                    arrow_forward
                  </span>
                </a>
              </div>
            </div>
          </div>
        </section>

        <section id="testimonials" className="py-24 sm:py-32 bg-gray-50">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-20">
              <h2 className="text-4xl sm:text-5xl font-bold text-gray-900">
                Echoes from the Future
              </h2>
              <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
                Hear from pioneers who've already made the leap.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="feature-card p-8 rounded-2xl flex flex-col">
                <p className="text-gray-700 mb-6 flex-grow">
                  "Axnore isn't an email client, it's a command center. The
                  predictive security has given our entire organization peace of
                  mind we never thought possible."
                </p>
                <div className="flex items-center mt-auto">
                  <img
                    alt="User avatar"
                    className="w-12 h-12 rounded-full mr-4 border-2 border-gray-300"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuB6sF3m8oruv0Iiq3XBjrEr2QomZ2Aozs1VIMrt4rWKojGiOzOH9CQfyHR-TAfQkjd6jX-Gbxzi72rg-UP66pOHTl0qlYLtZecFjjNAy9jbvOnJ4SNd8jK_YURjKC4r_p1jb_F6Wx-uIbYc9h1H9_sDcxFRpoQshpc0r1mAfrInx0LFjfqEQ0iu9wk4A2vC09wLSUcoqGbJ2UG-Q6zWEuUmEwmc2A7QX0x2lqyU2q2xhhOjer6lLzhh3L8w7myfcJiQbMApvMXI32Ch"
                  />
                  <div>
                    <p className="font-semibold text-gray-900">Sarah Jones</p>
                    <p className="text-gray-600 text-sm">CTO, Innovate Corp</p>
                  </div>
                </div>
              </div>
              <div className="feature-card p-8 rounded-2xl flex flex-col md:scale-105 md:border-indigo-500/80 bg-white">
                <p className="text-gray-700 mb-6 flex-grow">
                  "The AI Flow Composer is pure genius. It automated a client
                  onboarding sequence that used to take me hours per week. I'm
                  not just saving time, I'm scaling my business."
                </p>
                <div className="flex items-center mt-auto">
                  <img
                    alt="User avatar"
                    className="w-12 h-12 rounded-full mr-4 border-2 border-gray-300"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuCHEfgioTTC3z9bEZbK9ixUAcHDejVtzk8DR-z23Dn_rzyhw4MhlU6gjfL_6Mn_6hGBBKQSktWTL0NQ_vexFAwTJJBq1fktkm466y5XXbDAnnsRw74gpzilLAYGNumTj9v7E-qq5C7zmHCVfTJmPlDIv8VKEm1YS7aug_ZVlc8x-LmeqhXn68MfOJ9p4CdxlDcG24g-UiiXRYMLA65i4-iUt45na8GTkzY3ZwK6bHdSKPFMqJjXc-3O6Nv_oPDLEZdzLv_PoJ-dbEoJ"
                  />
                  <div>
                    <p className="font-semibold text-gray-900">Michael Chen</p>
                    <p className="text-gray-600 text-sm">
                      Founder, Nexus Dynamics
                    </p>
                  </div>
                </div>
              </div>
              <div className="feature-card p-8 rounded-2xl flex flex-col">
                <p className="text-gray-700 mb-6 flex-grow">
                  "I was skeptical about the 'Adaptive Inbox', but it's magical.
                  It's like my inbox knows what I need to focus on before I do.
                  My productivity and focus have skyrocketed."
                </p>
                <div className="flex items-center mt-auto">
                  <img
                    alt="User avatar"
                    className="w-12 h-12 rounded-full mr-4 border-2 border-gray-300"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuD56xvyvTBwaHDCBpIOlmcbjcrqm6k6TMVSa5pgTo1tuBRaQZoq6FClY-TTK_7aUzz092Z9q-9Cll2JRSWXPJPJPhsnEjAE47gZkmz2sFj1Gm8FFo3DIzYLdIw7jFDZA05rfJCo284_mYV9NCHQ-uNn-oLiFSAgLtEiIXvSQytsVuX8SB990gdjdySRyeyN9fmmBJ-X2212xqslqCD3b_1CwBjST2gt3ujn62163kF7Sb8zpJvUfWWFY1sK3Hj7fq89hKcCV29VWeFu"
                  />
                  <div>
                    <p className="font-semibold text-gray-900">
                      Emily Rodriguez
                    </p>
                    <p className="text-gray-600 text-sm">
                      Lead Digital Strategist
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32 text-center">
            <div className="relative bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-3xl p-10 sm:p-16 overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.1] z-0"></div>
              <div className="absolute -top-1/2 -left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-[spin_20s_linear_infinite] z-0"></div>
              <div className="relative z-10">
                <h2 className="text-4xl sm:text-5xl font-bold text-white">
                  Redefine Your Reality.
                </h2>
                <p className="mt-4 text-lg text-indigo-100 max-w-2xl mx-auto">
                  Step into the future of communication. It's time to stop
                  managing email and start commanding it.
                </p>
                <div className="mt-10">
                  <a
                    className="inline-flex items-center group bg-white text-indigo-600 px-10 py-4 rounded-xl font-bold text-lg shadow-2xl hover:bg-gray-100 transition-all transform hover:scale-105"
                    href="#"
                  >
                    <span>Claim Your Future Free</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-gray-100 text-gray-800">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
            <div className="col-span-2 lg:col-span-1">
              <a className="flex items-center space-x-2" href="#">
                <div className="w-8 h-8 flex items-center justify-center">
                  <svg
                    className="w-full h-full text-indigo-500"
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
                    ></path>
                    <path
                      d="M11.6667 19.9998L17.5 14.1665L23.3333 19.9998L29.1667 14.1665"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="3"
                    ></path>
                    <path
                      d="M11.6667 25.8332L17.5 19.9998L23.3333 25.8332L29.1667 19.9998"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="3"
                    ></path>
                  </svg>
                </div>
                <span className="text-2xl font-bold text-gray-900">Axnore</span>
              </a>
              <p className="mt-4 text-gray-600">
                Engineering the future of intelligent communication.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Product</h4>
              <ul className="mt-4 space-y-3">
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Security
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Integrations
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Company</h4>
              <ul className="mt-4 space-y-3">
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    About Us
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Careers
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Press
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Resources</h4>
              <ul className="mt-4 space-y-3">
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Blog
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Help Center
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    API Docs
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Legal</h4>
              <ul className="mt-4 space-y-3">
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Privacy
                  </a>
                </li>
                <li>
                  <a
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                    href="#"
                  >
                    Terms
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-16 border-t border-gray-200 pt-8 flex flex-col sm:flex-row justify-between items-center">
            <p className="text-gray-500">
              © 2024 Axnore. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 sm:mt-0">
              <a
                className="text-gray-500 hover:text-gray-800 transition-colors"
                href="#"
              >
                <svg
                  className="h-6 w-6"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.71v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
                </svg>
              </a>
              <a
                className="text-gray-500 hover:text-gray-800 transition-colors"
                href="#"
              >
                <svg
                  className="h-6 w-6"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12c0-5.523-4.477-10-10-10z"
                    fillRule="evenodd"
                  ></path>
                </svg>
              </a>
              <a
                className="text-gray-500 hover:text-gray-800 transition-colors"
                href="#"
              >
                <svg
                  className="h-6 w-6"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M16.6 5.9c.7 0 1.2.5 1.2 1.2s-.5 1.2-1.2 1.2-1.2-.5-1.2-1.2.5-1.2 1.2-1.2zm-4.6 2.5c-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4-1.8-4-4-4zm0 6.5c-1.4 0-2.5-1.1-2.5-2.5s1.1-2.5 2.5-2.5 2.5 1.1 2.5 2.5-1.1 2.5-2.5 2.5zM12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm6 12.9c0 .8-.1 1.5-.3 2.2-.3.9-.8 1.6-1.5 2.3s-1.4.9-2.3 1.2c-.7.2-1.4.3-2.2.3s-1.5-.1-2.2-.3c-.9-.3-1.6-.8-2.3-1.5s-.9-1.4-1.2-2.3c-.2-.7-.3-1.4-.3-2.2v-1.8c0-.8.1-1.5.3-2.2.3-.9.8-1.6 1.5-2.3s1.4-.9 2.3-1.2c.7-.2 1.4-.3 2.2-.3s1.5.1 2.2.3c.9.3 1.6.8 2.3 1.5s.9 1.4 1.2 2.3c.2.7.3 1.4.3 2.2v1.8z"></path>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* --- INLINE CUSTOM STYLES --- */}
      <style jsx global>{`
        :root {
          --glow-color: rgba(99, 102, 241, 0.4);
        }
        body {
          font-family: "Inter", sans-serif;
          background-color: #ffffff;
          color: #111827;
        }
        .hero-gradient {
          background: radial-gradient(
            ellipse at 50% 30%,
            #f9fafb 0%,
            #ffffff 70%
          );
        }
        #hero-canvas {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 1;
        }
        .nav-link {
          position: relative;
          transition: color 0.3s ease;
        }
        .nav-link::after {
          content: "";
          position: absolute;
          width: 0;
          height: 2px;
          bottom: -4px;
          left: 50%;
          transform: translateX(-50%);
          background-color: #6366f1;
          transition: width 0.3s ease;
        }
        .nav-link:hover::after {
          width: 100%;
        }
        @keyframes subtle-float {
          0%,
          100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }
        .floating-element {
          animation: subtle-float 6s ease-in-out infinite;
        }
        @keyframes pulse-glow {
          0%,
          100% {
            box-shadow:
              0 0 20px 5px var(--glow-color),
              0 0 40px 10px var(--glow-color),
              0 0 60px 15px transparent;
          }
          50% {
            box-shadow:
              0 0 30px 8px var(--glow-color),
              0 0 50px 15px var(--glow-color),
              0 0 70px 20px transparent;
          }
        }
        .glow-pulse {
          animation: pulse-glow 5s ease-in-out infinite;
        }
        @keyframes fadeInDown {
          from {
            opacity: 0;
            transform: translateY(-30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeInDown {
          animation: fadeInDown 1s ease-out forwards;
        }
        .delay-200 {
          animation-delay: 0.2s;
        }
        .delay-400 {
          animation-delay: 0.4s;
        }
        .logo-animate {
          animation: logo-glow 4s ease-in-out infinite;
        }
        @keyframes logo-glow {
          0% {
            filter: drop-shadow(0 0 2px rgba(129, 140, 248, 0.7));
            transform: scale(1);
          }
          50% {
            filter: drop-shadow(0 0 8px rgba(129, 140, 248, 1))
              drop-shadow(0 0 15px rgba(129, 140, 248, 0.5));
            transform: scale(1.05);
          }
          100% {
            filter: drop-shadow(0 0 2px rgba(129, 140, 248, 0.7));
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}
