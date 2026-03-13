"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  BookOpen, 
  Users, 
  FileText, 
  BarChart3,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import './adminStyles.css';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<{ email: string; username: string } | null>(null);

  // Получаем данные пользователя из localStorage
  useEffect(() => {
    const userData = localStorage.getItem('admin_user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    // Очищаем cookie и localStorage
    document.cookie = 'admin_token=; path=/; max-age=0';
    localStorage.removeItem('admin_user');
    router.push('/admin/login');
  };

  const navItems = [
    { href: '/admin', label: 'Дашборд', icon: LayoutDashboard },
    { href: '/admin/words', label: 'Слова', icon: BookOpen },
    { href: '/admin/users', label: 'Пользователи', icon: Users },
    { href: '/admin/diary', label: 'Дневник', icon: FileText },
    { href: '/admin/stats', label: 'Статистика', icon: BarChart3 },
  ];

  return (
    <div className="adminLayout">
      {/* Mobile menu button */}
      <button
        className="adminBtn adminBtnSecondary"
        style={{
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: 100,
          display: 'none',
        }}
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside className={`adminSidebar ${sidebarOpen ? 'adminSidebarOpen' : ''}`}>
        <div className="adminSidebarHeader">
          <h1 className="adminSidebarTitle">KlarDeutsch Admin</h1>
          <p className="adminSidebarSubtitle">Панель управления</p>
        </div>

        <nav className="adminNav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`adminNavItem ${isActive ? 'adminNavItemActive' : ''}`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className="adminNavItemIcon" size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="adminUserSection">
          <div className="adminUserInfo">
            <div className="adminUserAvatar">
              {user?.username?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="adminUserDetails">
              <div className="adminUserName">{user?.username || 'Admin'}</div>
              <div className="adminUserEmail">{user?.email || 'admin@klardeutsch.com'}</div>
            </div>
          </div>
          <button className="adminLogoutBtn" onClick={handleLogout}>
            <LogOut size={16} style={{ marginRight: 8 }} />
            Выйти
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="adminMain">
        <header className="adminHeader">
          <div>
            <h2 className="adminHeaderTitle">
              {navItems.find(item => item.href === pathname)?.label || 'Админ-панель'}
            </h2>
            <p className="adminHeaderSubtitle">
              {new Date().toLocaleDateString('ru-RU', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
        </header>

        <div className="adminContent">
          {children}
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            zIndex: 90,
          }}
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
