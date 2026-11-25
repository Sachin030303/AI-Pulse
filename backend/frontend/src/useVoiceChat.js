import { useCallback, useEffect, useRef, useState } from 'react';

function speechError(code) {
  const errors = {
    'not-allowed': 'Microphone access was denied. Allow microphone permission for 127.0.0.1:5173 in your browser.',
    'service-not-allowed': 'The browser speech recognition service is unavailable or blocked.',
    'audio-capture': 'No usable microphone was found. Check your Windows microphone settings.',
    'no-speech': 'No speech was detected. Try again and speak clearly.',
    'network': 'Speech recognition could not reach its service. Check your connection or browser settings.',
    'language-not-supported': 'This language is not supported by the browser recognition service.',
    'aborted': 'Voice recognition was cancelled.',
  };
  return errors[code] || `Speech recognition stopped (${code || 'unknown error'}).`;
}

function spokenText(value) {
  return String(value || '')
    .replace(/```[\s\S]*?```/g, ' Code example omitted. ')
    .replace(/https?:\/\/\S+/gi, ' link omitted ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_#>|]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 1800);
}

export function useVoiceChat({ onFinalTranscript, onPartialTranscript, onError }) {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef('');
  const callbacksRef = useRef({ onFinalTranscript, onPartialTranscript, onError });
  callbacksRef.current = { onFinalTranscript, onPartialTranscript, onError };

  const recognitionSupported = typeof window !== 'undefined' &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  const speakingSupported = typeof window !== 'undefined' &&
    'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

  const stopSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }, []);

  const speak = useCallback((answer, requestedLanguage = 'en-IN') => {
    if (!speakingSupported) {
      callbacksRef.current.onError('Speech playback is unavailable in this browser.');
      return;
    }
    const text = spokenText(answer);
    if (!text) return;

    stopSpeaking();
    const language = /[\u0900-\u097F]/.test(text) ? 'hi-IN' :
      (requestedLanguage === 'hi-IN' ? 'en-IN' : requestedLanguage);
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 1;
    utterance.pitch = 1;

    const voices = window.speechSynthesis.getVoices();
    const match = voices.find(voice => voice.lang.toLowerCase() === language.toLowerCase()) ||
      voices.find(voice => voice.lang.toLowerCase().startsWith(language.slice(0, 2).toLowerCase()));
    if (match) utterance.voice = match;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [speakingSupported, stopSpeaking]);

  const stopListening = useCallback(() => {
    try { recognitionRef.current?.stop(); }
    catch { recognitionRef.current = null; setListening(false); }
  }, []);

  const startListening = useCallback((language = 'en-IN') => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      callbacksRef.current.onError('Microphone speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }
    if (recognitionRef.current) return;

    stopSpeaking();
    finalTranscriptRef.current = '';
    let failed = false;
    const recognition = new Recognition();
    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onresult = (event) => {
      const finalPieces = [];
      const interimPieces = [];
      for (let i = 0; i < event.results.length; i += 1) {
        const piece = event.results[i]?.[0]?.transcript?.trim();
        if (!piece) continue;
        if (event.results[i].isFinal) finalPieces.push(piece);
        else interimPieces.push(piece);
      }
      finalTranscriptRef.current = finalPieces.join(' ').slice(0, 3000);
      callbacksRef.current.onPartialTranscript(
        [...finalPieces, ...interimPieces].join(' ').slice(0, 3000),
      );
    };
    recognition.onerror = (event) => {
      failed = true;
      if (event.error !== 'aborted') callbacksRef.current.onError(speechError(event.error));
    };
    recognition.onend = () => {
      recognitionRef.current = null;
      setListening(false);
      const transcript = finalTranscriptRef.current.trim();
      finalTranscriptRef.current = '';
      if (!failed && transcript) callbacksRef.current.onFinalTranscript(transcript);
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
      setListening(true);
    } catch {
      recognitionRef.current = null;
      setListening(false);
      callbacksRef.current.onError('Could not start the microphone. Check browser microphone permission.');
    }
  }, [stopSpeaking]);

  useEffect(() => () => {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      try { recognition.abort(); } catch { /* Already stopped. */ }
      recognitionRef.current = null;
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }, []);

  return {
    listening, speaking, recognitionSupported, speakingSupported,
    startListening, stopListening, speak, stopSpeaking,
  };
}
