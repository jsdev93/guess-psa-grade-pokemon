/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: { soft: "0 8px 24px rgba(0,0,0,.06)" },
    },
  },
  plugins: [],
};
