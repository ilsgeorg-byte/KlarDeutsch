"use client";

import React from "react";
import styles from "./styles/Shared.module.css";


export default function HomePage() {
  return (
    // Добавляем min-h-screen и flex flex-col, чтобы растянуть страницу на весь экран
    <div className={`${styles.pageWrapper} min-h-screen flex flex-col`}>

      {/* Контент главной. Добавляем flex-1, чтобы этот блок отталкивал Footer вниз */}
      <main
        className={`${styles.container} flex-1 flex flex-col items-center justify-center`}
        style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto', padding: '60px 20px' }}
      >
        <h1 className="text-slate-800 dark:text-white" style={{ fontSize: '3.5rem', fontWeight: '800', marginBottom: '24px', lineHeight: '1.2' }}>
          Учи немецкий <span className="text-blue-600 dark:text-blue-400" style={{ color: '#2563eb' }}>легко</span>
        </h1>

        <p className="text-slate-600 dark:text-gray-300" style={{ fontSize: '1.25rem', lineHeight: '1.6', marginBottom: '48px', maxWidth: '600px' }}>
          Твой персональный помощник для уровня A1.
          Тренируй слова, записывай произношение и веди записи.
        </p>

        <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/trainer" className="dark:bg-blue-500 dark:hover:bg-blue-600" style={{
            textDecoration: 'none',
            background: '#2563eb',
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
          <a href="/diary" className="dark:bg-gray-800 dark:text-blue-400 dark:border-gray-600" style={{
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


    </div>
  );
}
