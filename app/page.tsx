"use client";

import React from "react";
import styles from "./styles/Shared.module.css"; 

export default function HomePage() {
  return (
    <div className={styles.pageWrapper}>
      {/* Шапка (такая же как в тренажере) */}
      <header className={styles.header}>
        <a href="/" className={styles.logo}>
          <span>🇩🇪</span> KlarDeutsch
        </a>
        <nav className={styles.nav}>
          <a href="/" className={styles.navLink}>Главная</a>
          {/* Ссылка на текущую страницу (Тренажер) */}
          <a href="/trainer" className={styles.navLink}>Тренажер</a>
          {/* Добавленная ссылка на страницу аудио */}
          <a href="/audio" className={styles.navLink}>Записи</a>
        </nav>
      </header>

      {/* Контент главной */}
      <main className={styles.container} style={{ textAlign: 'center', maxWidth: '800px' }}>
        <h1 style={{ fontSize: '3rem', color: '#2c3e50', marginBottom: '24px' }}>
          Учи немецкий <span style={{ color: '#3498db' }}>легко</span>
        </h1>
        
        <p style={{ fontSize: '1.2rem', color: '#555', lineHeight: '1.6', marginBottom: '40px' }}>
          Твой персональный помощник для уровня A1. 
          Тренируй слова, записывай произношение и следи за прогрессом.
        </p>

        <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/trainer" style={{ 
            textDecoration: 'none', 
            background: '#3498db', 
            color: 'white', 
            padding: '16px 32px', 
            borderRadius: '12px', 
            fontWeight: '600',
            fontSize: '1.1rem',
            boxShadow: '0 4px 15px rgba(52, 152, 219, 0.3)',
            transition: 'transform 0.2s'
          }}
          onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
          onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            Начать тренировку слов →
          </a>
        </div>
      </main>
    </div>
  );
}
