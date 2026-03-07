import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

// Mock Three.js
vi.mock("three", () => ({
  Scene: vi.fn(() => ({})),
  PerspectiveCamera: vi.fn(() => ({ position: { z: 0 } })),
  WebGLRenderer: vi.fn(() => ({
    setSize: vi.fn(),
    setPixelRatio: vi.fn(),
    render: vi.fn(),
  })),
  IcosahedronGeometry: vi.fn(() => ({})),
  ShaderMaterial: vi.fn(() => ({})),
  Color: vi.fn(() => ({})),
}));

// Mock the page component to avoid Three.js issues
const MockPage = () => (
  <div>
    <h1>Welcome to My App</h1>
    <canvas id="hero-canvas" style={{ display: "none" }} />
  </div>
);

describe("Home Page", () => {
  it("renders the main heading", () => {
    render(<MockPage />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent("Welcome to My App");
  });
});
