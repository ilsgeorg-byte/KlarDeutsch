"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  const [isLoaded, setIsLoaded] = useState(false);

  // Загрузка темы из localStorage при монтировании
  useEffect(() => {
    const saved = localStorage.getItem('globalTheme');
    if (saved === 'dark' || saved === 'light') {
      setTheme(saved);
    }
    setIsLoaded(true);
  }, []);

  // Сохранение темы и применение класса
  useEffect(() => {
    if (!isLoaded) return;

    localStorage.setItem('globalTheme', theme);

    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      console.log('🌙 Dark theme applied');
    } else {
      document.documentElement.classList.remove('dark');
      console.log('☀️ Light theme applied');
    }
  }, [theme, isLoaded]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
