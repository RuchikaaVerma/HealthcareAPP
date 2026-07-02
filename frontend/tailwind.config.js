/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0B1220",       // deep clinical-night base
        teal: {
          DEFAULT: "#13B8A6",
          dim: "#0E8C7E",
          glow: "#5EEAD4",
        },
        periwinkle: {
          DEFAULT: "#7C9CFF",
          dim: "#5B7CE0",
        },
        clinical: {
          DEFAULT: "#F4F7F9",
          dim: "#E4EAEE",
        },
        coral: {
          DEFAULT: "#FF6B6B",
          dim: "#E25555",
        },
        surface: {
          DEFAULT: "#111B2E",  // card surface, slightly lighter than ink
          raised: "#162338",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "radial-fade": "radial-gradient(circle at 50% 0%, rgba(19,184,166,0.15), transparent 60%)",
      },
      boxShadow: {
        glow: "0 0 40px rgba(19,184,166,0.25)",
        "glow-periwinkle": "0 0 40px rgba(124,156,255,0.25)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        float: "float 6s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
    },
  },
  plugins: [],
};
