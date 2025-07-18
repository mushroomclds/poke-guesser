 /** @type {import('tailwindcss').Config} */
 module.exports = {
  content: ['./src/**/*.{html,js,ts}'],
  theme: {
    extend: {animation: {
        'fade-in': 'fadeIn 0.7s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["dark"], 
  },
};
