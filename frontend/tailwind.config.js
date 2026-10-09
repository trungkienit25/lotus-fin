/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        satoshi: ["Outfit", "system-ui", "-apple-system", "sans-serif"],
      },
      colors: {
        // Lotus Fin Official Brand Scale (Centered on #1E63B7 Blue Deep)
        brand: {
          25: "#f5f9ff",
          50: "#f0f7ff",
          100: "#e0effe",
          200: "#bae0fd",
          300: "#6EC1F6", // Blue Light
          400: "#38acf7",
          500: "#1E63B7", // Primary Brand Anchor (Blue Deep)
          600: "#174f96",
          700: "#143f79",
          800: "#133663",
          900: "#152f53",
        },
        // Lotus Specific Semantic Tokens (Brand Guideline)
        lotus: {
          blue: "#1E63B7",
          "blue-light": "#6EC1F6",
          teal: "#39C6B7",
          mint: "#2FB29A",
          pink: "#FF8FB1",
          "pink-light": "#FFDDE7",
          "text-primary": "#2E3A59",
          "text-secondary": "#8FA1B3",
          bg: "#E8F2FB",
        },
        gray: {
          25: "#fcfcfd",
          50: "#f9fafb",
          100: "#f2f4f7",
          200: "#e4e7ec",
          300: "#d0d5dd",
          400: "#98a2b3",
          500: "#667085",
          600: "#475467",
          700: "#344054",
          800: "#1d2939",
          900: "#101828",
          dark: "#1a2231",
        },
        success: {
          50: "#ecfdf3",
          100: "#d1fadf",
          500: "#2FB29A", // Lotus Mint Green
          600: "#24937f",
        },
        error: {
          50: "#fef3f2",
          100: "#fee4e2",
          500: "#f04438",
          600: "#d92d20",
        },
        warning: {
          50: "#fffaeb",
          100: "#fef0c7",
          500: "#f79009",
          600: "#dc6803",
        },
        primary: "#1E63B7",
      },
      backgroundImage: {
        "lotus-primary": "linear-gradient(90deg, #1E63B7 0%, #6EC1F6 50%, #2FB29A 100%)",
        "lotus-primary-135": "linear-gradient(135deg, #1E63B7 0%, #6EC1F6 50%, #2FB29A 100%)",
        "lotus-accent": "linear-gradient(90deg, #FFDDE7 0%, #FF8FB1 100%)",
        "lotus-soft": "linear-gradient(180deg, rgba(232, 242, 251, 0.7) 0%, rgba(255, 255, 255, 0) 100%)",
      },
      boxShadow: {
        "theme-xs": "0px 1px 2px 0px rgba(16, 24, 40, 0.05)",
        "theme-sm": "0px 1px 3px 0px rgba(16, 24, 40, 0.1), 0px 1px 2px 0px rgba(16, 24, 40, 0.06)",
        "theme-md": "0px 4px 8px -2px rgba(16, 24, 40, 0.1), 0px 2px 4px -2px rgba(16, 24, 40, 0.06)",
        "theme-lg": "0px 12px 16px -4px rgba(16, 24, 40, 0.08), 0px 4px 6px -2px rgba(16, 24, 40, 0.03)",
        "theme-xl": "0px 20px 24px -4px rgba(16, 24, 40, 0.08), 0px 8px 8px -4px rgba(16, 24, 40, 0.03)",
      },
    },
  },
  plugins: [],
};
