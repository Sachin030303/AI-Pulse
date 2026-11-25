import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity, ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, CalendarDays,
  CheckCircle2, ChevronDown, ChevronLeft, ChevronRight, CircleAlert,
  Clock3, ExternalLink, FileText, Filter, FolderKanban, Layers3, LayoutDashboard,
  ListTodo, LoaderCircle, LockKeyhole, LogOut, Menu, MessageSquareText,
  Newspaper, RefreshCw, Search, Send, Settings, ShieldCheck, Sparkles,
  Target, TrendingUp, X,
} from 'lucide-react';
import { Mic, Square, Volume2, VolumeX } from 'lucide-react';
import { useVoiceChat } from './useVoiceChat.js';
import { apiRequest, getSavedToken, saveToken } from './api.js';
import { formatDate, friendlyError, safeUrl, shortText } from './utils.js';

const NAV = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'news', label: 'AI News', icon: Newspaper },
  { id: 'briefings', label: 'Daily Briefings', icon: FileText },
  { id: 'assistant', label: 'AI Assistant', icon: MessageSquareText },
  { id: 'workspace', label: 'My Workspace', icon: FolderKanban },
  { id: 'settings', label: 'Settings', icon: Settings },
];
const CATEGORIES = [
  'All', 'AI Models', 'AI Agents', 'Research', 'Robotics',
  'Infrastructure', 'Startups & Funding', 'Products & Releases',
  'Policy & Regulation', 'Industry News', 'Other',
];

function Brand({ expanded = true }) {
  return <div className="brand">
    <div className="brand-icon"><Activity size={22} strokeWidth={2.7} /></div>
    {expanded && <div><span className="brand-name">AI<span>Pulse</span></span><div className="brand-tagline">PERSONAL INTELLIGENCE</div></div>}
  </div>;
}
function ErrorNote({ message, onRetry }) {
  if (!message) return null;
  return <div className="error-note" role="alert"><CircleAlert size={17}/><span>{message}</span>{onRetry && <button className="text-action" onClick={onRetry}>Retry</button>}</div>;
}
function Loading({ label = 'Loading…' }) {
  return <div className="loading-state"><LoaderCircle className="spin" size={23}/><span>{label}</span></div>;
}
function Empty({ title, description, icon: Icon = BookOpen }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={26}/></div><strong>{title}</strong><span>{description}</span></div>;
}
function StatusChip({ value }) {
  return <span className={`status-chip ${String(value || '').toLowerCase().replace(/[^a-z]+/g, '-')}`}>{value || 'Unknown'}</span>;
}
function SectionHeading({ eyebrow, title, description, right }) {
  return <div className="section-heading">
    <div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>
    {right && <div className="section-actions">{right}</div>}
  </div>;
}
function IconButton({ icon: Icon, label, className = '', ...props }) {
  return <button type="button" className={`icon-button ${className}`} title={label} aria-label={label} {...props}><Icon size={18}/></button>;
}

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const result = await apiRequest('/auth/login', { method: 'POST', body: { email: email.trim(), password } });
      if (!result?.access_token) throw new Error('The login response did not include a token.');
      onLogin(result.access_token);
    } catch (err) { setError(friendlyError(err)); }
    finally { setBusy(false); }
  };
  return <div className="login-layout">
    <div className="login-glow glow-one"/><div className="login-glow glow-two"/>
    <div className="login-left">
      <Brand />
      <div className="login-story">
        <span className="hero-pill"><Sparkles size={15}/> YOUR PRIVATE AI WORKSPACE</span>
        <h1>Stay ahead of<br/><em>what's next.</em></h1>
        <p>One calm place for AI news, research insights, daily briefings and everything you're building.</p>
        <div className="feature-list">
          <div><span><Newspaper size={18}/></span> Real-time AI news intelligence</div>
          <div><span><Sparkles size={18}/></span> Gemini-powered research and briefings</div>
          <div><span><FolderKanban size={18}/></span> Projects, skills and progress in sync</div>
        </div>
      </div>
      <div className="login-footnote"><ShieldCheck size={15}/> Local-first · Your existing AI-Pulse backend</div>
    </div>
    <div className="login-right"><div className="login-card">
      <div className="login-card-icon"><LockKeyhole size={23}/></div>
      <h2>Welcome back</h2><p>Sign in with your existing AI-Pulse administrator account.</p>
      <form onSubmit={submit}>
        <label htmlFor="login-email">Email address</label>
        <input id="login-email" autoComplete="username" type="email" required value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" />
        <label htmlFor="login-password">Password</label>
        <input id="login-password" autoComplete="current-password" type="password" required value={password} onChange={event => setPassword(event.target.value)} placeholder="Enter your password" />
        <ErrorNote message={error}/>
        <button type="submit" className="primary-button full-width" disabled={busy}>{busy ? <LoaderCircle className="spin" size={18}/> : <ArrowRight size={18}/>} Sign in to AI-Pulse</button>
      </form>
      <div className="login-help">Email-based password recovery is not configured in this personal setup.</div>
    </div></div>
  </div>;
}

function Overview({ token, goTo }) {
  const [data, setData] = useState({});
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    const result = await Promise.allSettled([
      apiRequest('/knowledge/stats', { token }),
      apiRequest('/projects/stats', { token }),
      apiRequest('/skills/stats', { token }),
      apiRequest('/briefings/latest', { token }),
    ]);
    const names = ['knowledge', 'projects', 'skills', 'latest'];
    const values = {}; const failures = [];
    result.forEach((item, index) => {
      if (item.status === 'fulfilled') values[names[index]] = item.value;
      else if (!(names[index] === 'latest' && item.reason?.status === 404)) failures.push(`${names[index]}: ${friendlyError(item.reason)}`);
    });
    setData(values); setErrors(failures); setLoading(false);
  }, [token]);
  useEffect(() => { load(); }, [load]);
  const latest = data.latest?.briefing;
  return <>
    <SectionHeading eyebrow="YOUR DAILY PULSE" title={<>Good to have you here<span className="heading-dot">.</span></>} description="A clear view of your AI universe, all in one place." right={<button className="secondary-button" onClick={load}><RefreshCw size={16}/> Refresh</button>} />
    <div className="welcome-banner"><div><span className="banner-label"><Sparkles size={15}/> INTELLIGENCE, ORGANIZED</span><h2>Turn today's AI noise into<br/><span>your next big idea.</span></h2><p>Explore what's new, distill the important stories, and keep your personal projects moving.</p><button className="banner-button" onClick={() => goTo('news')}>Explore AI news <ArrowUpRight size={17}/></button></div><div className="banner-art" aria-hidden="true"><div className="orb orb-one"/><div className="orb orb-two"/><div className="orb orb-three"/><Activity size={95}/></div></div>
    {errors.length > 0 && <ErrorNote message={errors.join(' · ')} onRetry={load}/>}
    <div className="metrics-grid">
      <Metric title="Tracked articles" icon={Newspaper} number={data.knowledge?.total_articles} hint="In your research library" loading={loading}/>
      <Metric title="Classified articles" icon={Layers3} number={data.knowledge?.classified_articles} hint="Organized by AI topic" loading={loading}/>
      <Metric title="My projects" icon={FolderKanban} number={data.projects?.total_projects} hint="Your active workstreams" loading={loading}/>
      <Metric title="My skills" icon={TrendingUp} number={data.skills?.total_skills} hint="Learning and developing" loading={loading}/>
    </div>
    <div className="overview-columns">
      <div className="panel"><div className="panel-header"><div><span className="eyebrow">AI RESEARCH</span><h3>Latest daily briefing</h3></div><IconButton icon={ArrowUpRight} label="Open briefings" onClick={() => goTo('briefings')}/></div>
        {loading ? <Loading/> : latest ? <><div className="meta-row"><span><CalendarDays size={14}/> {formatDate(data.latest.date)}</span><span><BookOpen size={14}/> {latest.sources_used ?? 0} sources</span></div><p className="briefing-excerpt">{shortText(latest.briefing, 680)}</p><button className="quiet-link" onClick={() => goTo('briefings')}>Read full briefing <ArrowRight size={15}/></button></> : <Empty icon={FileText} title="No saved briefing yet" description="A briefing will appear here after a scheduled or manual pipeline run."/>}
      </div>
      <div className="panel"><div className="panel-header"><div><span className="eyebrow">YOUR MOMENTUM</span><h3>Keep building</h3></div><IconButton icon={ArrowUpRight} label="Open workspace" onClick={() => goTo('workspace')}/></div>
        <div className="progress-facts"><div><span>Projects completed</span><strong>{data.projects?.completed ?? '—'}</strong></div><div><span>Tasks completed</span><strong>{data.projects?.completed_tasks ?? '—'}</strong></div><div><span>Overall project progress</span><strong>{data.projects?.overall_progress != null ? `${Math.round(data.projects.overall_progress)}%` : '—'}</strong></div></div>
        <button className="quiet-link" onClick={() => goTo('workspace')}>Go to my workspace <ArrowRight size={15}/></button>
      </div>
    </div>
  </>;
}
function Metric({ title, icon: Icon, number, hint, loading }) {
  return <div className="metric-card"><div className="metric-top"><span>{title}</span><div className="metric-icon"><Icon size={18}/></div></div><strong>{loading ? '···' : number ?? '—'}</strong><span className="metric-hint">{hint}</span></div>;
}

function News({ token }) {
  const [searchDraft, setSearchDraft] = useState('');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All');
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [articleId, setArticleId] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    apiRequest('/news/', { token, signal: controller.signal, params: { page, page_size: 12, q: query, category: category === 'All' ? '' : category } })
      .then(setResult)
      .catch(err => { if (err.name !== 'AbortError') setError(friendlyError(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [token, page, query, category, refreshKey]);
  return <>
    <SectionHeading eyebrow="DISCOVER & UNDERSTAND" title="AI News Explorer" description="Find signal in the noise. Your curated AI news library." right={<button className="secondary-button" onClick={() => setRefreshKey(value => value + 1)}><RefreshCw size={16}/> Refresh</button>}/>
    <div className="search-bar"><Search size={19}/><form onSubmit={e => { e.preventDefault(); setPage(1); setQuery(searchDraft.trim()); }}><input aria-label="Search AI news" placeholder="Search headlines, topics, research…" value={searchDraft} onChange={e => setSearchDraft(e.target.value)}/><button type="submit">Search</button></form></div>
    <div className="category-row" aria-label="Filter by category">{CATEGORIES.map(value => <button key={value} className={`category-chip ${category === value ? 'active' : ''}`} onClick={() => { setCategory(value); setPage(1); }}>{value}</button>)}</div>
    <div className="results-heading"><span>{loading ? 'Loading articles…' : `${result?.total ?? 0} articles found`}</span><span><Filter size={14}/> Page {page} of {result?.pages ?? 1}</span></div>
    <ErrorNote message={error} onRetry={() => setRefreshKey(value => value + 1)}/>
    {loading ? <Loading label="Fetching your AI news…"/> : result?.items?.length ? <div className="news-grid">{result.items.map(item => <button className="news-card" key={item.id} onClick={() => setArticleId(item.id)}>
      <div className="news-card-top"><span className="category-tag">{item.category || 'Uncategorized'}</span><ArrowUpRight size={17}/></div>
      <h3>{item.title}</h3><p>{shortText(item.summary || item.content || 'Open this article to read more.', 190)}</p>
      <div className="news-card-bottom"><span><Clock3 size={14}/> {formatDate(item.published_at || item.created_at)}</span><span className="read-story">Read story <ChevronRight size={15}/></span></div>
    </button>)}</div> : !error && <Empty title="No articles found" description="Try a different search or category. New stories arrive when your pipeline runs." icon={Newspaper}/>}
    <div className="pagination"><button className="secondary-button" disabled={page <= 1 || loading} onClick={() => setPage(p => p - 1)}><ChevronLeft size={17}/> Previous</button><span>Page {page} / {Math.max(result?.pages ?? 1, 1)}</span><button className="secondary-button" disabled={loading || page >= (result?.pages ?? 1)} onClick={() => setPage(p => p + 1)}>Next <ChevronRight size={17}/></button></div>
    {articleId && <ArticleDialog id={articleId} token={token} onClose={() => setArticleId(null)}/>}
  </>;
}
function ArticleDialog({ id, token, onClose }) {
  const [article, setArticle] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    apiRequest(`/news/${id}`, { token, signal: controller.signal }).then(setArticle).catch(err => { if (err.name !== 'AbortError') setError(friendlyError(err)); });
    const onEsc = event => { if (event.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onEsc);
    return () => { controller.abort(); document.removeEventListener('keydown', onEsc); };
  }, [id, token, onClose]);
  const external = safeUrl(article?.url);
  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section className="article-dialog" role="dialog" aria-modal="true" aria-label="Article details"><div className="dialog-top"><Brand/><IconButton icon={X} label="Close article" onClick={onClose}/></div>
    <ErrorNote message={error}/>{!article && !error ? <Loading/> : article && <div className="dialog-content"><span className="category-tag">{article.category || 'AI News'}</span><h2>{article.title}</h2><div className="meta-row"><span><CalendarDays size={14}/> {formatDate(article.published_at)}</span><span><ShieldCheck size={14}/> {article.is_verified ? 'Verified' : 'Not verified'}</span></div>{article.summary && <p className="article-lead">{article.summary}</p>}<div className="article-body">{article.content || 'Full extracted article content is not available yet.'}</div>{external && <a className="primary-button read-original" href={external} target="_blank" rel="noopener noreferrer">Open original source <ExternalLink size={17}/></a>}</div>}
  </section></div>;
}

function Briefings({ token }) {
  const [latest, setLatest] = useState(null);
  const [generated, setGenerated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setLatest(await apiRequest('/briefings/latest', { token })); }
    catch (err) { if (err.status !== 404) setError(friendlyError(err)); }
    finally { setLoading(false); }
  }, [token]);
  useEffect(() => { load(); }, [load]);
  const generate = async () => {
    setBusy(true); setError('');
    try {
      const item = await apiRequest('/briefing/generate', { token, method: 'POST', body: { days: 7, max_articles: 5 } });
      setGenerated(item);
    } catch (err) { setError(friendlyError(err)); }
    finally { setBusy(false); }
  };
  const data = generated || latest?.briefing;
  return <>
    <SectionHeading eyebrow="YOUR AI DIGEST" title="Daily Intelligence Briefings" description="Gemini distills your AI news into clear, actionable context." right={<div className="button-group"><button className="secondary-button" onClick={load}><RefreshCw size={16}/> Saved</button><button className="primary-button" onClick={generate} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16}/> : <Sparkles size={16}/>} Generate now</button></div>}/>
    <div className="info-strip"><Sparkles size={18}/><span>Generate now makes a fresh Gemini API request and may consume quota. The daily scheduled pipeline saves its briefing automatically.</span></div>
    <ErrorNote message={error}/>
    {loading && !generated ? <Loading label="Loading saved briefing…"/> : data ? <div className="briefing-layout"><div className="panel briefing-panel"><div className="briefing-header"><span className="hero-pill"><Sparkles size={15}/> {generated ? 'FRESHLY GENERATED' : 'SAVED DAILY BRIEFING'}</span><span className="briefing-date"><CalendarDays size={16}/> {formatDate(generated ? data.generated_at : latest.date)}</span></div><h2>Your AI landscape, in focus.</h2><div className="meta-row"><span><BookOpen size={15}/> {data.sources_used ?? data.sources?.length ?? 0} sources</span><span><Clock3 size={15}/> {data.period_days ?? 7} day window</span>{data.model && <span><Sparkles size={15}/> {data.model}</span>}</div><div className="briefing-body">{data.briefing || 'This briefing returned no text.'}</div></div>
      <div className="panel sources-panel"><span className="eyebrow">REFERENCES</span><h3>Sources used</h3>{data.sources?.length ? <div className="source-list">{data.sources.map((source, index) => { const href = safeUrl(source.url); return <div key={index} className="source-row"><span className="source-number">{String(index + 1).padStart(2, '0')}</span><div><strong>{source.title || source.source_name || `Source ${index + 1}`}</strong>{href && <a href={href} target="_blank" rel="noopener noreferrer">View source <ExternalLink size={13}/></a>}</div></div>; })}</div> : <p className="muted">No source details were returned.</p>}</div></div> : <Empty title="No briefing saved yet" description="Run the AI-Pulse pipeline with --with-briefing, or select Generate now." icon={FileText}/>}
  </>;
}

function Assistant({ token }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [voiceLanguage, setVoiceLanguage] = useState('en-IN');
  const [speakVoiceReplies, setSpeakVoiceReplies] = useState(true);
  const runningRef = useRef(false);
  const requestRef = useRef(null);

  const {
    listening, speaking, recognitionSupported, speakingSupported,
    startListening, stopListening, speak, stopSpeaking,
  } = useVoiceChat({
    onPartialTranscript: (transcript) => setInput(transcript),
    onFinalTranscript: (transcript) => { void sendQuestion(transcript, true); },
    onError: setVoiceError,
  });

  const sendQuestion = async (text, fromVoice = false) => {
    const question = String(text || '').trim().slice(0, 3000);
    if (!question || runningRef.current) return;
    runningRef.current = true;
    setBusy(true);
    setInput('');
    setVoiceError('');
    stopSpeaking();

    const controller = new AbortController();
    requestRef.current = controller;
    const id = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setMessages(list => [...list, { id: id(), type: 'user', text: question }]);

    try {
      const result = await apiRequest('/chat/ask', {
        token, method: 'POST', body: { message: question }, signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      const answer = result.answer || 'No answer returned.';
      setMessages(list => [...list, {
        id: id(), type: 'assistant', text: answer,
        sources: result.sources || [], model: result.model,
      }]);
      if (fromVoice && speakVoiceReplies && speakingSupported) speak(answer, voiceLanguage);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages(list => [...list, {
          id: id(), type: 'error', text: friendlyError(err),
        }]);
      }
    } finally {
      runningRef.current = false;
      if (requestRef.current === controller) requestRef.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  };

  useEffect(() => () => {
    requestRef.current?.abort();
  }, []);

  const send = (event) => {
    event.preventDefault();
    if (listening) return;
    void sendQuestion(input, false);
  };

  return <>
    <SectionHeading eyebrow="GEMINI + VOICE" title="Your AI Research Assistant"
      description="Talk to AI-Pulse or type a question grounded in your collected AI news." />
    <div className="chat-shell">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-starter">
            <div className="chat-logo"><Sparkles size={30}/></div>
            <h2>What would you like to understand?</h2>
            <p>Ask by voice or text about models, agents, research, product releases, and AI trends.</p>
            <div className="prompt-grid">
              {[
                'What are the biggest developments in AI this week?',
                'Summarize recent AI agent news',
                'What research should I pay attention to?',
              ].map(prompt => (
                <button key={prompt} onClick={() => setInput(prompt)}>
                  {prompt}<ArrowUpRight size={16}/>
                </button>
              ))}
            </div>
          </div>
        ) : messages.map(item => (
          <div key={item.id} className={`chat-message ${item.type}`}>
            <div className="chat-avatar">
              {item.type === 'user' ? 'You' : <Sparkles size={18}/>}
            </div>
            <div className="chat-bubble">
              {item.text}
              {item.model && <div className="chat-model">Model: {item.model}</div>}
              {item.sources?.length > 0 && (
                <div className="chat-sources">
                  {item.sources.slice(0, 5).map((source, index) => {
                    const href = safeUrl(source.url);
                    return href ? <a key={index} href={href} target="_blank" rel="noopener noreferrer">
                      {shortText(source.title || 'Source', 55)} <ExternalLink size={12}/>
                    </a> : null;
                  })}
                </div>
              )}
              {item.type === 'assistant' && speakingSupported && (
                <button type="button" className="voice-replay"
                  onClick={() => speaking ? stopSpeaking() : speak(item.text, voiceLanguage)}
                  aria-label={speaking ? 'Stop reading response' : 'Read response aloud'}>
                  {speaking ? <VolumeX size={15}/> : <Volume2 size={15}/>}
                  {speaking ? 'Stop reading' : 'Read aloud'}
                </button>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="chat-message assistant">
            <div className="chat-avatar"><Sparkles size={18}/></div>
            <div className="chat-bubble"><LoaderCircle className="spin" size={18}/> Thinking with Gemini…</div>
          </div>
        )}
      </div>
      <form className="chat-composer" onSubmit={send}>
        <input aria-label="Ask AI-Pulse" value={input} onChange={event => setInput(event.target.value)}
          placeholder={listening ? 'Listening to your voice…' : 'Ask anything about your AI news…'}
          maxLength={3000} />
        {recognitionSupported && (
          <button type="button" className={`voice-button ${listening ? 'is-listening' : ''}`}
            disabled={busy} onClick={() => {
              setVoiceError('');
              if (listening) stopListening();
              else startListening(voiceLanguage);
            }} aria-label={listening ? 'Stop microphone and send' : 'Start voice question'}
            title={listening ? 'Stop and send your voice question' : 'Talk to AI-Pulse'}>
            {listening ? <Square size={17}/> : <Mic size={20}/>}
          </button>
        )}
        <button className="send-button" type="submit"
          disabled={!input.trim() || busy || listening} aria-label="Send question">
          <Send size={19}/>
        </button>
      </form>
      <div className="voice-controls">
        <div className="voice-options">
          {recognitionSupported ? (
            <label className="voice-language">
              Voice language
              <select value={voiceLanguage} onChange={event => setVoiceLanguage(event.target.value)}
                disabled={listening || busy}>
                <option value="en-IN">English (India)</option>
                <option value="en-US">English (US)</option>
                <option value="hi-IN">Hindi (India)</option>
              </select>
            </label>
          ) : <span className="voice-available-note">Voice recognition is not available in this browser. Try Chrome or Edge.</span>}
          {speakingSupported && (
            <label className="voice-toggle">
              <input type="checkbox" checked={speakVoiceReplies}
                onChange={event => setSpeakVoiceReplies(event.target.checked)}/>
              Speak replies to voice questions
            </label>
          )}
        </div>
        <p className="voice-status" role="status">
          {listening ? 'Listening… Speak your question, then pause or click Stop & send.' :
            speaking ? 'Speaking… Use Stop reading to interrupt.' :
            recognitionSupported ? 'Click the microphone to speak.' : ''}
        </p>
      </div>
      {voiceError && <p className="voice-warning" role="alert">{voiceError}</p>}
      <div className="chat-footnote">
        Microphone access requires permission. Depending on your browser, speech recognition may use a
        cloud service. Gemini receives your transcribed text, not a recorded audio file.
        Conversations are not persisted in this version.
      </div>
    </div>
  </>;
}

function Workspace({ token }) {
  const [tab, setTab] = useState('projects');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [tasks, setTasks] = useState(null);
  const [taskError, setTaskError] = useState('');
  const [key, setKey] = useState(0);
  const endpoints = { projects: '/projects/', skills: '/skills/', goals: '/progress/goals' };
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setData(null); setError(''); setSelected(null); setTasks(null);
    apiRequest(endpoints[tab], { token, signal: controller.signal, params: { page: 1, page_size: 30 } })
      .then(setData).catch(err => { if (err.name !== 'AbortError') setError(friendlyError(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [tab, token, key]);
  const openProject = async project => {
    setSelected(project); setTasks(null); setTaskError('');
    try { setTasks(await apiRequest(`/projects/${project.id}/tasks`, { token, params: { page: 1, page_size: 50 } })); }
    catch (err) { setTaskError(friendlyError(err)); }
  };
  return <>
    <SectionHeading eyebrow="MAKE PROGRESS" title="My Workspace" description="The projects you're building and the skills you're growing." right={<button className="secondary-button" onClick={() => setKey(v => v + 1)}><RefreshCw size={16}/> Refresh</button>}/>
    <div className="tabs" role="tablist" aria-label="Workspace views">{[{ id: 'projects', label: 'Projects', icon: FolderKanban }, { id: 'skills', label: 'Skills', icon: TrendingUp }, { id: 'goals', label: 'Learning Goals', icon: Target }].map(item => <button key={item.id} className={`tab ${tab === item.id ? 'active' : ''}`} role="tab" aria-selected={tab === item.id} onClick={() => setTab(item.id)}><item.icon size={17}/>{item.label}</button>)}</div>
    <ErrorNote message={error}/>
    {loading ? <Loading label="Loading your workspace…"/> : data?.items?.length ? <div className="workspace-grid">{data.items.map(item => <button className="workspace-card" key={item.id} onClick={() => tab === 'projects' && openProject(item)} disabled={tab !== 'projects'}><div className="workspace-card-heading"><span className="workspace-icon">{tab === 'projects' ? <FolderKanban size={20}/> : tab === 'skills' ? <BookOpen size={20}/> : <Target size={20}/>}</span><StatusChip value={item.status}/></div><h3>{item.name || item.title}</h3><p>{shortText(item.description || item.category || 'No description added yet.', 130)}</p><div className="workspace-card-bottom"><span>{item.category || item.priority || ''}</span>{typeof item.progress === 'number' && <strong>{Math.round(item.progress)}%</strong>}</div>{typeof item.progress === 'number' && <div className="progress-track"><div style={{ width: `${Math.max(0, Math.min(100, item.progress))}%` }}/></div>}{tab === 'projects' && <span className="view-tasks">View tasks <ArrowUpRight size={14}/></span>}</button>)}</div> : !error && <Empty title="Nothing here yet" description="Items you create through your existing APIs will appear here." icon={FolderKanban}/>}
    {selected && tab === 'projects' && <div className="panel task-panel"><div className="panel-header"><div><span className="eyebrow">PROJECT TASKS</span><h3>{selected.name}</h3></div><IconButton icon={X} label="Close tasks" onClick={() => setSelected(null)}/></div><ErrorNote message={taskError}/>{tasks ? tasks.items?.length ? <div className="task-list">{tasks.items.map(task => <div className="task-item" key={task.id}><ListTodo size={18}/><div><strong>{task.title}</strong><span>{shortText(task.description, 130)}</span></div><StatusChip value={task.status}/></div>)}</div> : <Empty title="No tasks added" description="Add tasks through your project API." icon={ListTodo}/> : !taskError && <Loading label="Fetching project tasks…"/>}</div>}
  </>;
}
function Preferences({ profile, onSignOut }) {
  return <><SectionHeading eyebrow="PERSONAL SETUP" title="Settings" description="Your local AI-Pulse environment and account."/>
    <div className="settings-grid"><div className="panel"><div className="panel-header"><div><span className="eyebrow">ACCOUNT</span><h3>Signed-in user</h3></div><ShieldCheck size={20}/></div><div className="setting-row"><span>Email</span><strong>{profile?.email || '—'}</strong></div><div className="setting-row"><span>Role</span><StatusChip value={profile?.role}/></div><div className="setting-row"><span>Session</span><span className="active-dot">Active</span></div><button className="secondary-button danger" onClick={onSignOut}><LogOut size={16}/> Sign out</button></div>
      <div className="panel"><div className="panel-header"><div><span className="eyebrow">LOCAL AUTOMATION</span><h3>Daily pipeline</h3></div><Clock3 size={20}/></div><p className="muted">Your Windows Task Scheduler entry is configured separately from this dashboard. The UI does not currently read live task status.</p><div className="setting-row"><span>Configured task</span><strong>AI-Pulse Daily Intelligence</strong></div><div className="setting-row"><span>Daily trigger</span><strong>9:00 AM local time</strong></div><div className="setting-note">Windows task scheduling requires a logged-in session with your chosen task principal.</div></div></div>
    <div className="info-strip"><ShieldCheck size={19}/><span>Your login token is stored in this browser tab's session storage, not sent to external services. Keep AI-Pulse bound to 127.0.0.1 for this personal setup.</span></div>
  </>;
}

function Dashboard({ token, profile, onSignOut }) {
  const [view, setView] = useState('overview');
  const [menuOpen, setMenuOpen] = useState(false);
  const title = NAV.find(item => item.id === view)?.label || 'Overview';
  const renderView = () => {
    switch (view) {
      case 'overview': return <Overview token={token} goTo={setView}/>;
      case 'news': return <News token={token}/>;
      case 'briefings': return <Briefings token={token}/>;
      case 'assistant': return <Assistant token={token}/>;
      case 'workspace': return <Workspace token={token}/>;
      case 'settings': return <Preferences profile={profile} onSignOut={onSignOut}/>;
      default: return null;
    }
  };
  return <div className="app-shell"><aside className={`sidebar ${menuOpen ? 'open' : ''}`}><div className="sidebar-top"><Brand/><IconButton className="mobile-close" icon={X} label="Close menu" onClick={() => setMenuOpen(false)}/></div><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{NAV.map(item => <button key={item.id} className={`nav-item ${view === item.id ? 'active' : ''}`} onClick={() => { setView(item.id); setMenuOpen(false); }}><item.icon size={20}/><span>{item.label}</span>{view === item.id && <span className="nav-active-indicator"/>}</button>)}</nav><div className="sidebar-bottom"><div className="sidebar-note"><Sparkles size={19}/><strong>Intelligence that compounds.</strong><span>Fresh insights, every day.</span></div><button className="sidebar-user" onClick={() => setView('settings')}><span className="avatar">{profile?.email?.[0]?.toUpperCase() || 'A'}</span><span><strong>{profile?.email?.split('@')[0] || 'My account'}</strong><small>{profile?.role || 'AI-Pulse'}</small></span><ChevronRight size={17}/></button></div></aside>
    {menuOpen && <button className="mobile-shade" aria-label="Close navigation" onClick={() => setMenuOpen(false)}/>}
    <div className="app-main"><header className="topbar"><div className="topbar-left"><IconButton className="mobile-menu" icon={Menu} label="Open menu" onClick={() => setMenuOpen(true)}/><span className="breadcrumb-home">AI-Pulse</span><ChevronRight size={14}/><span>{title}</span></div><div className="topbar-right"><span className="online-indicator"><span/> Personal workspace</span><span className="topbar-avatar">{profile?.email?.[0]?.toUpperCase() || 'A'}</span></div></header><main className="content">{renderView()}<footer className="main-footer">AI-Pulse · Personal AI Intelligence <span>Built on your FastAPI + PostgreSQL + Gemini stack</span></footer></main></div>
  </div>;
}

export default function App() {
  const [token, setToken] = useState(getSavedToken);
  const [profile, setProfile] = useState(null);
  const [checking, setChecking] = useState(Boolean(token));
  const signOut = useCallback(() => { saveToken(''); setProfile(null); setToken(''); setChecking(false); }, []);
  const signIn = useCallback(value => { saveToken(value); setToken(value); setChecking(true); }, []);
  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    setChecking(true);
    apiRequest('/auth/me', { token, signal: controller.signal })
      .then(data => { setProfile(data); setChecking(false); })
      .catch(err => {
        if (err.name === 'AbortError') return;
        if (err.status === 401) signOut();
        else { setProfile(null); setChecking(false); }
      });
    return () => controller.abort();
  }, [token, signOut]);
  if (!token) return <LoginPage onLogin={signIn}/>;
  if (checking) return <div className="auth-loading"><Brand/><Loading label="Connecting to AI-Pulse…"/></div>;
  if (!profile) return <div className="auth-loading"><Brand/><ErrorNote message="Could not verify your session. Confirm FastAPI is running, then retry."/><button className="secondary-button" onClick={() => { setChecking(true); apiRequest('/auth/me', {token}).then(setProfile).catch(() => setChecking(false)); }}>Retry</button><button className="quiet-link" onClick={signOut}>Sign out</button></div>;
  return <Dashboard token={token} profile={profile} onSignOut={signOut}/>;
}
