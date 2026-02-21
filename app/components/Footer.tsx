"use client";

import Link from "next/link";
import { BookOpen, Mail, Heart } from "lucide-react";

export default function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="w-full bg-white border-t border-slate-200 mt-auto">
            <div className="max-w-6xl mx-auto px-6 py-8 md:py-12">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">

                    {/* Колонка 1: Логотип и описание */}
                    <div className="flex flex-col gap-4">
                        <Link href="/" className="flex items-center gap-2">
                            <div className="bg-blue-600 text-white p-2 rounded-xl">
                                <BookOpen size={24} />
                            </div>
                            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-600">
                                KlarDeutsch
                            </span>
                        </Link>
                        <p className="text-slate-500 text-sm leading-relaxed">
                            Умный тренажер немецкого языка.
                            Учи слова эффективно с помощью карточек,
                            интервального повторения и примеров от ИИ.
                        </p>
                    </div>

                    {/* Колонка 2: Навигация */}
                    <div className="flex flex-col gap-3">
                        <h3 className="font-semibold text-slate-800 mb-2">Навигация</h3>
                        <Link href="/" className="text-slate-500 hover:text-blue-600 text-sm transition-colors w-fit">
                            Главная
                        </Link>
                        <Link href="/dictionary" className="text-slate-500 hover:text-blue-600 text-sm transition-colors w-fit">
                            Словарь
                        </Link>
                        <Link href="/trainer" className="text-slate-500 hover:text-blue-600 text-sm transition-colors w-fit">
                            Тренажер
                        </Link>
                    </div>

                    {/* Колонка 3: Контакты */}
                    <div className="flex flex-col gap-3">
                        <h3 className="font-semibold text-slate-800 mb-2">Связь</h3>
                        <a
                            href="mailto:hello@klardeutsch.app"
                            className="flex items-center gap-2 text-slate-500 hover:text-blue-600 text-sm transition-colors w-fit"
                        >
                            <Mail size={16} />
                            hello@klardeutsch.app
                        </a>
                    </div>
                </div>

                {/* Нижняя полоса с копирайтом */}
                <div className="pt-8 border-t border-slate-100 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-slate-400 text-sm">
                        © {currentYear} KlarDeutsch. Все права защищены.
                    </p>
                    <p className="text-slate-400 text-sm flex items-center gap-1.5">
                        Сделано с <Heart size={14} className="text-red-500 fill-red-500" /> для изучения немецкого
                    </p>
                </div>
            </div>
        </footer>
    );
}
