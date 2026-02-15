"use client";

import React, { useEffect, useState } from "react";
import styles from "../styles/Shared.module.css"; // Путь на уровень выше

export default function AudioPage() {
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadFiles = async () => {
    try {
      const res = await fetch("http://127.0.0.1:5000/api/list_audio");
      const data = await res.json();
      setFiles(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { loadFiles(); }, []);

  const deleteFile = async (filename: string) => {
    if (!confirm("Удалить запись?")) return;
    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    await fetch(`${apiUrl}/api/delete_audio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename })
    });
    await loadFiles();
    setLoading(false);
  };

  return (
    <div className={styles.pageWrapper}>
      <header className={styles.header}>
        <a href="/" className={styles.logo}>
          <span>🇩🇪</span> KlarDeutsch
        </a>
        <nav className={styles.nav}>
          <a href="/" className={styles.navLink}>Главная</a>
          {/* Ссылка на текущую страницу (Тренажер) */}
          <a href="/trainer" className={`${styles.navLink} ${styles.navLinkActive}`}>Тренажер</a>
          {/* Добавленная ссылка на страницу аудио */}
          <a href="/audio" className={styles.navLink}>Записи</a>
        </nav>
      </header>

      <main className={styles.container}>
        <h1 className={styles.pageTitle}>Мои записи</h1>
        
        {files.length === 0 ? (
          <p style={{textAlign: 'center', color: '#888'}}>Нет записей</p>
        ) : (
          <div style={{display: 'flex', flexDirection: 'column', gap: '15px'}}>
            {files.map(file => (
              <div key={file} className={styles.card} style={{
                minHeight: 'auto', 
                padding: '20px', 
                flexDirection: 'row', 
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{display: 'flex', flexDirection: 'column', gap: '5px', flex: 1}}>
                  <span className={styles.label}>{file}</span>
                  <audio controls src={`/api/files/${file}`} style={{height: '30px', maxWidth: '250px'}} />
                </div>
                
                <button 
                  onClick={() => deleteFile(file)}
                  className={styles.btn}
                  style={{
                    flex: '0 0 auto', 
                    background: '#fee2e2', 
                    color: '#991b1b', 
                    padding: '10px 15px',
                    fontSize: '0.8rem',
                    marginLeft: '15px'
                  }}
                  disabled={loading}
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
