import { createContext, useState, useContext } from "react";

export const ThemeContext = createContext();

export function ThemeProvider({ children }) {
    const [isDark, setIsDark] = useState(
        () => localStorage.getItem("theme") === "dark"
    );

    const toggleTheme = () => {
        setIsDark(prev => {
            const next = !prev;
            localStorage.setItem("theme", next ? "dark" : "light");
            return next;
        });
    };

    return (
        <ThemeContext.Provider value={{ isDark, toggleTheme }}>
            <div className={isDark ? "theme-dark" : "theme-light"} style={{ minHeight: "100vh" }}>
                {children}
            </div>
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    return useContext(ThemeContext);
}
