"use client";

import React from "react";
import styles from "./styles/Shared.module.css";
import Header from "./components/Header";
import Footer from "./components/Footer"; // <-- Импортируем наш новый Footer

export default function HomePage() {
  return (
    // Добавляем min-h-screen и flex flex-col, чтобы растянуть страницу на весь экран
    <div className={`${styles.pageWrapper} min-h-screen flex flex-col`}>
      <Header />

      {/* Контент главной. Добавляем flex-1, чтобы этот блок отталкивал Footer вниз */}
      <main
        className={`${styles.container} flex-1 flex flex-col items-center justify-center`}
        style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto', padding: '60px 20px' }}
      >
        <h1 style={{ fontSize: '3.5rem', fontWeight: '800', color: '#1e293b', marginBottom: '24px', lineHeight: '1.2' }}>
          Учи немецкий <span style={{ color: '#2563eb' }}>легко</span>
        </h1>

        <p style={{ fontSize: '1.25rem', color: '#64748b', lineHeight: '1.6', marginBottom: '48px', maxWidth: '600px' }}>
          Твой персональный помощник для уровня A1.
          Тренируй слова, записывай произношение и веди дневник.
        </p>

        <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/trainer" style={{
            textDecoration: 'none',
            background: '#2563eb', // Обновил цвет под современный синий (blue-600)
            color: 'white',
            padding: '16px 32px',
            borderRadius: '16px',
            fontWeight: '600',
            fontSize: '1.1rem',
            boxShadow: '0 10px 25px -5px rgba(37, 99, 235, 0.4)',
            transition: 'all 0.2s ease-in-out'
          }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-3px)';
              e.currentTarget.style.boxShadow = '0 15px 30px -5px rgba(37, 99, 235, 0.5)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 10px 25px -5px rgba(37, 99, 235, 0.4)';
            }}
          >
            Начать тренировку →
          </a>
          <a href="/diary" style={{
            textDecoration: 'none',
            background: 'white',
            color: '#2563eb',
            padding: '16px 32px',
            borderRadius: '16px',
            fontWeight: '600',
            fontSize: '1.1rem',
            border: '2px solid #e2e8f0',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
            transition: 'all 0.2s ease-in-out'
          }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-3px)';
              e.currentTarget.style.borderColor = '#2563eb';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.borderColor = '#e2e8f0';
            }}
          >
            Заметки ✍️
          </a>
        </div>
      </main>

      <Footer /> {/* <-- Подвал будет аккуратно прижат к низу */}
    </div>
  );
}
