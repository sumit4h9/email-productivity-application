import { useEffect, useRef } from "react";
import * as THREE from "three";
import { Button } from "@/components/ui/button";

const HeroSection = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<{
    scene?: THREE.Scene;
    camera?: THREE.PerspectiveCamera;
    renderer?: THREE.WebGLRenderer;
    mesh?: THREE.Mesh;
    animationId?: number;
  }>({});

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 2.5;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Create animated geometry
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

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Store references
    sceneRef.current = { scene, camera, renderer, mesh };

    // Mouse interaction
    let mouseX = 0,
      mouseY = 0;
    const handleMouseMove = (event: MouseEvent) => {
      mouseX = (event.clientX - window.innerWidth / 2) * 0.0005;
      mouseY = (event.clientY - window.innerHeight / 2) * 0.0005;
    };

    document.addEventListener("mousemove", handleMouseMove);

    // Animation loop
    const clock = new THREE.Clock();
    const animate = () => {
      const elapsedTime = clock.getElapsedTime();

      if (mesh && material.uniforms) {
        material.uniforms.uTime.value = elapsedTime;
        mesh.rotation.y = elapsedTime * 0.05;
        mesh.rotation.x = elapsedTime * 0.05;
      }

      camera.position.x += (mouseX - camera.position.x) * 0.05;
      camera.position.y += (-mouseY - camera.position.y) * 0.05;
      camera.lookAt(scene.position);

      renderer.render(scene, camera);
      sceneRef.current.animationId = requestAnimationFrame(animate);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      if (sceneRef.current.animationId) {
        cancelAnimationFrame(sceneRef.current.animationId);
      }
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <section className="relative hero-gradient text-foreground min-h-screen flex items-center justify-center overflow-hidden">
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full z-10"
      />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-20 text-center pt-24 sm:pt-32">
        <div className="animate-fadeInDown">
          <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-tight bg-clip-text text-transparent bg-gradient-to-br from-foreground to-muted-foreground">
            Beyond Inbox.
          </h1>
          <h2 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-primary-light mt-2">
            Enter Axnore.
          </h2>
        </div>

        <p className="mt-8 max-w-3xl mx-auto text-lg sm:text-xl text-muted-foreground animate-fadeInDown delay-200">
          An intelligent email experience that adapts to you. Powered by
          next-generation AI to deliver unparalleled productivity, security, and
          a touch of magic.
        </p>

        <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6 animate-fadeInDown delay-400">
          <Button className="w-full sm:w-auto bg-primary text-primary-foreground px-10 py-4 text-lg font-bold shadow-2xl shadow-primary/30 transition-all transform hover:scale-105 hover:shadow-primary/50">
            Experience the Future
          </Button>
          <Button
            variant="outline"
            className="w-full sm:w-auto border-2 border-border text-foreground px-10 py-4 text-lg font-bold hover:bg-muted hover:border-muted-foreground transition-colors"
          >
            Watch Demo
          </Button>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
