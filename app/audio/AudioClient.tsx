"use client";

/**
 * Клиентский компонент для работы с аудио
 * Вынесен отдельно для оптимизации (Server Components)
 */

import React, { useState, useCallback } from "react";
import styles from "../styles/Shared.module.css";

interface AudioClientProps {
  initialFiles: string[];
}

export default function AudioClient({ initialFiles }: AudioClientProps) {
  const [files, setFiles] = useState<string[]>(initialFiles);
  const [loading, setLoading] = useState(false);

  const loadFiles = useCallback(async (token: string) => {
    try {
      const res = await fetch("/api/list_audio", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFiles(data);
      }
    } catch (e) {
      console.error("Ошибка загрузки:", e);
    }
  }, []);

  const deleteFile = useCallback(async (filename: string) => {
    if (!confirm("Удалить запись?")) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const res = await fetch("/api/delete_audio", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ filename })
      });

      if (res.ok) {
        setFiles(prev => prev.filter(f => f !== filename));
      } else {
        alert("Ошибка при удалении");
      }
    } catch (e) {
      console.error("Ошибка удаления:", e);
      alert("Ошибка сети");
    } finally {
      setLoading(false);
    }
  }, []);

  if (files.length === 0) {
    return (
      <p style={{ textAlign: 'center', color: '#888', padding: '40px' }}>
        Нет записей
      </p>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
      {files.map(file => (
        <div 
          key={file} 
          className={styles.card} 
          style={{
            minHeight: 'auto',
            padding: '20px',
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'default'
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', flex: 1 }}>
            <span className={styles.label}>{file}</span>
            <audio 
              controls 
              src={`/api/files/${file}`} 
              style={{ height: '30px', maxWidth: '250px' }}
              preload="metadata"
            />
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
            aria-label={`Удалить ${file}`}
          >
            Удалить
          </button>
        </div>
      ))}
    </div>
  );
}
