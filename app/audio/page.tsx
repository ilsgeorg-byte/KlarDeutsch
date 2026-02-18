"use client";

import React, { useEffect, useState } from "react";
import styles from "../styles/Shared.module.css"; // Путь на уровень выше

import Header from "../components/Header";

export default function AudioPage() {
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadFiles = async () => {
    try {
      const res = await fetch("/api/list_audio");
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
    try {
      const res = await fetch("/api/delete_audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename })
      });
      if (res.ok) {
        await loadFiles();
      } else {
        alert("Ошибка при удалении");
      }
    } catch (e) {
      console.error("Ошибка удаления:", e);
      alert("Ошибка сети");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.pageWrapper}>
      <Header />

      <main className={styles.container}>
        <h1 className={styles.pageTitle}>Мои записи</h1>

        {files.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#888' }}>Нет записей</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {files.map(file => (
              <div key={file} className={styles.card} style={{
                minHeight: 'auto',
                padding: '20px',
                flexDirection: 'row',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', flex: 1 }}>
                  <span className={styles.label}>{file}</span>
                  <audio controls src={`/api/files/${file}`} style={{ height: '30px', maxWidth: '250px' }} />
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
