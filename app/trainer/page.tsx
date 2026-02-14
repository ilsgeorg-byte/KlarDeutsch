"use client";

import { useState, useEffect, useRef } from "react";
import { Mic, Square, Volume2, ArrowRight, Eye, EyeOff } from "lucide-react";

// Описываем, как выглядит слово
interface Word {
  id: number;
  de: string;
  ru: string;
  example_de?: string;
  example_ru?: string;
  level: string;
}

export default function TrainerPage() {
  // --- Состояние (State) ---
  const [words, setWords] = useState<Word[]>([]);
  const [level, setLevel] = useState("A1"); // Выбранный уровень
  const [index, setIndex] = useState(0); // Текущее слово (номер в массиве)
  const [showAnswer, setShowAnswer] = useState(false); // Показать перевод?
  const [loading, setLoading] = useState(false); // Идет ли загрузка?
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  
  // Для записи голоса (если нужно)
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  // --- Загрузка слов при смене уровня ---
  useEffect(() => {
    const loadWords = async () => {
      setLoading(true);
      setAudioStatus(null);
      try {
        // Запрашиваем API с нужным уровнем
        const res = await fetch(`/api/index?action=words&level=${level}`);
        if (!res.ok) throw new Error("Ошибка загрузки");
        
        const data = await res.json();
        setWords(data);
        setIndex(0); // Сбрасываем на первое слово
        setShowAnswer(false); // Скрываем ответ
      } catch (e) {
        console.error(e);
        setAudioStatus("Не удалось загрузить слова");
        setWords([]);
      } finally {
        setLoading(false);
      }
    };

    loadWords();
  }, [level]); // <-- Перезапускать, когда меняется level

  // --- Управление ---
  const handleNext = () => {
    setShowAnswer(false);
    setAudioStatus(null);
    setIndex((prev) => (prev + 1) % words.length); // Циклический переход
  };

  const playAudio = (text: string) => {
    // Простая озвучка браузером
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "de-DE";
    window.speechSynthesis.speak(utterance);
  };

  const currentWord = words[index];

  // --- Рендер (JSX) ---
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      
      {/* Заголовок */}
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Тренажер слов</h1>

      {/* 1. КНОПКИ УРОВНЕЙ */}
      <div className="flex flex-wrap gap-2 mb-8 justify-center">
        {["A1", "A2", "B1", "B2", "C1"].map((lvl) => (
          <button
            key={lvl}
            onClick={() => setLevel(lvl)}
            className={`px-4 py-2 rounded-lg font-bold transition-all shadow-sm ${
              level === lvl
                ? "bg-blue-600 text-white scale-105 shadow-md"
                : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
            }`}
          >
            {lvl}
          </button>
        ))}
      </div>

      {/* 2. ГЛАВНАЯ КАРТОЧКА */}
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden min-h-[400px] flex flex-col relative">
        
        {loading ? (
          // Состояние загрузки
          <div className="flex-1 flex items-center justify-center flex-col gap-4">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-gray-500">Загружаем слова {level}...</p>
          </div>
        ) : !currentWord ? (
          // Состояние "Слов нет"
          <div className="flex-1 flex items-center justify-center flex-col p-8 text-center">
            <p className="text-xl text-gray-600 mb-4">Слов для уровня {level} пока нет.</p>
            <p className="text-sm text-gray-400">Попробуйте выбрать другой уровень или добавить слова в базу.</p>
          </div>
        ) : (
          // Состояние "Слово есть"
          <div className="flex-1 flex flex-col p-8">
            
            {/* Немецкое слово */}
            <div className="flex-1 flex flex-col items-center justify-center text-center mb-8">
              <h2 className="text-5xl font-bold text-gray-800 mb-4 break-words w-full">
                {currentWord.de}
              </h2>
              
              {/* Кнопка озвучки */}
              <button
                onClick={() => playAudio(currentWord.de)}
                className="p-3 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition-colors"
                title="Прослушать"
              >
                <Volume2 size={24} />
              </button>
            </div>

            {/* Блок ответа (скрытый/открытый) */}
            <div 
              className={`transition-all duration-300 ease-in-out overflow-hidden ${
                showAnswer ? "max-h-60 opacity-100 mb-6" : "max-h-0 opacity-0"
              }`}
            >
              <div className="bg-gray-50 p-4 rounded-xl text-center border border-gray-100">
                <p className="text-2xl text-green-700 font-medium mb-2">
                  {currentWord.ru}
                </p>
                {currentWord.example_de && (
                  <div className="text-sm text-gray-500 mt-3 pt-3 border-t border-gray-200">
                    <p className="italic mb-1">{currentWord.example_de}</p>
                    <p className="opacity-75">{currentWord.example_ru}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Нижняя панель кнопок */}
            <div className="grid grid-cols-2 gap-4 mt-auto">
              {/* Кнопка Показать/Скрыть */}
              <button
                onClick={() => setShowAnswer(!showAnswer)}
                className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold transition-colors ${
                  showAnswer 
                    ? "bg-gray-100 text-gray-700 hover:bg-gray-200" 
                    : "bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-blue-500/30"
                }`}
              >
                {showAnswer ? <EyeOff size={20} /> : <Eye size={20} />}
                {showAnswer ? "Скрыть" : "Перевод"}
              </button>

              {/* Кнопка Далее */}
              <button
                onClick={handleNext}
                className="flex items-center justify-center gap-2 py-3 px-4 bg-gray-800 text-white rounded-xl font-semibold hover:bg-black transition-colors"
              >
                <span>Далее</span>
                <ArrowRight size={20} />
              </button>
            </div>

            {/* Статус бар (для ошибок или микрофона) */}
            {(audioStatus || isRecording) && (
               <div className="absolute top-0 left-0 w-full p-2 text-center text-xs font-medium bg-yellow-100 text-yellow-800">
                 {isRecording ? "Запись..." : audioStatus}
               </div>
            )}
            
          </div>
        )}
      </div>
      
      {/* Счетчик слов */}
      {!loading && words.length > 0 && (
        <p className="mt-6 text-gray-400 text-sm font-medium">
          Слово {index + 1} из {words.length}
        </p>
      )}
    </div>
  );
}
