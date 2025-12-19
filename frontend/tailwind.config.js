/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                eve: {
                    bg: "#0A0A0A",
                    panel: "#121212",
                    border: "#333333",
                    accent: {
                        blue: "#00AEEF", // EVE UI Blue
                        orange: "#F5A623", // EVE Warn/Orange
                        red: "#E02020", // Killmail Red
                    },
                    text: "#E0E0E0",
                    muted: "#888888"
                }
            },
            fontFamily: {
                sans: ['"Inter"', 'sans-serif'], // Or 'Roboto' if preferred, default to clean sans
            }
        },
    },
    plugins: [],
}
