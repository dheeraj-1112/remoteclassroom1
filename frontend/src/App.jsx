import { useEffect, useState } from 'react'
import {
  Activity, Bell, BookOpen, CalendarDays, ChevronRight, Film, GraduationCap,
  LayoutDashboard, LogOut, Menu, Plus, Search, UploadCloud,
} from 'lucide-react'
import api, { errorMessage, unwrapList } from './api'
import Modal from './components/Modal'
import VideoPlayer from './components/VideoPlayer'

const initialUser = () => {
  try { return JSON.parse(localStorage.getItem('rc_user') || 'null') } catch { return null }
}

function StatusPill({ status }) {
  const value = (status || 'waiting').toLowerCase()
  return <span className={`status-pill ${value}`}>{value.replace('_', ' ')}</span>
}

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const change = (key) => (event) => setForm((old) => ({ ...old, [key]: event.target.value }))

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const { data } = await api.post(mode === 'login' ? '/auth/login/' : '/auth/register/', form)
      localStorage.setItem('rc_token', data.token)
      localStorage.setItem('rc_user', JSON.stringify(data.user))
      onLogin(data.user)
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <div className="auth-page">
      <div className="auth-brand"><div className="brand-mark">RC</div><div><b>Remote Classroom</b><span>Learning without the bandwidth barrier</span></div></div>
      <div className="auth-layout">
        <div className="auth-intro">
          <div className="eyebrow">BANDWIDTH-ADAPTIVE LEARNING</div>
          <h1>Good learning should not depend on a perfect internet connection.</h1>
          <p>Access recorded lectures, scheduled live classes and lecture summaries in one place. Use Lite Mode when video streaming is difficult.</p>
          <div className="intro-points"><span><BookOpen size={17}/> Recorded lectures</span><span><Activity size={17}/> Lite Mode summaries</span><span><CalendarDays size={17}/> Scheduled live classes</span></div>
        </div>
        <form className="auth-card" onSubmit={submit}>
          <div className="auth-tabs"><button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Sign in</button><button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Student registration</button></div>
          <h2>{mode === 'login' ? 'Welcome back' : 'Create a student account'}</h2>
          <p className="muted">{mode === 'login' ? 'Sign in to continue to your classroom.' : 'Student accounts can enroll in subjects after registration.'}</p>
          {mode === 'register' && <><label>First name<input value={form.first_name} onChange={change('first_name')} /></label><label>Last name<input value={form.last_name} onChange={change('last_name')} /></label><label>Email<input type="email" required value={form.email} onChange={change('email')} /></label></>}
          <label>Username<input required autoComplete="username" value={form.username} onChange={change('username')} /></label>
          <label>Password<input required type="password" minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={form.password} onChange={change('password')} /></label>
          {error && <div className="error-box">{error}</div>}
          <button className="primary-button full-width" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'} <ChevronRight size={17}/></button>
          <p className="auth-footnote">Faculty accounts are created by the project administrator.</p>
        </form>
      </div>
      <footer className="auth-footer">Tech Fusion · B.Tech CSE · 2023–2027</footer>
    </div>
  )
}

function App() {
  const [user, setUser] = useState(initialUser)
  const [page, setPage] = useState('overview')
  const [selectedLecture, setSelectedLecture] = useState(null)
  const [mobileNav, setMobileNav] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const role = user?.role || 'student'
  const faculty = role === 'faculty'

  useEffect(() => {
    if (!localStorage.getItem('rc_token')) return
    api.get('/auth/me/').then(({ data }) => { setUser(data); localStorage.setItem('rc_user', JSON.stringify(data)) }).catch(() => signOut())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function signOut() {
    api.post('/auth/logout/').catch(() => {})
    localStorage.removeItem('rc_token'); localStorage.removeItem('rc_user'); setUser(null)
  }

  const nav = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'subjects', label: 'Subjects', icon: BookOpen },
    { id: 'lectures', label: 'Lectures', icon: GraduationCap },
    { id: 'live', label: 'Live classes', icon: CalendarDays },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ]

  function refresh() { setRefreshKey((value) => value + 1) }
  function openLecture(lecture) { setSelectedLecture(lecture); setPage('lecture-detail') }

  if (!user) return <AuthScreen onLogin={setUser} />

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
        <div className="sidebar-brand"><div className="brand-mark small-mark">RC</div><div><b>Remote Classroom</b><span>Tech Fusion</span></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav>{nav.map((item) => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => { setPage(item.id); setSelectedLecture(null); setMobileNav(false) }}><item.icon size={18}/>{item.label}{item.id === 'notifications' && <span className="nav-dot"/>}</button>)}</nav>
        <div className="sidebar-bottom"><div className="user-card"><div className="avatar">{(user.full_name || user.username).slice(0, 1).toUpperCase()}</div><div className="user-meta"><b>{user.full_name || user.username}</b><span>{faculty ? 'Faculty' : 'Student'}</span></div><button className="icon-button logout" onClick={signOut} title="Sign out"><LogOut size={17}/></button></div></div>
      </aside>
      <main className="main-area">
        <header className="topbar"><button className="icon-button mobile-menu" onClick={() => setMobileNav((v) => !v)}><Menu size={20}/></button><div className="breadcrumb">Workspace <ChevronRight size={14}/><b>{selectedLecture ? 'Lecture details' : nav.find((n) => n.id === page)?.label || 'Overview'}</b></div><div className="topbar-right"><span className="role-tag">{faculty ? 'FACULTY VIEW' : 'STUDENT VIEW'}</span><div className="top-avatar">{(user.full_name || user.username).slice(0, 1).toUpperCase()}</div></div></header>
        <div className="page-container">
          {page === 'overview' && <Overview user={user} faculty={faculty} onNavigate={setPage} onOpenLecture={openLecture} refreshKey={refreshKey}/>}
          {page === 'subjects' && <Subjects faculty={faculty} onChange={refresh} refreshKey={refreshKey}/>}
          {page === 'lectures' && <Lectures faculty={faculty} onOpenLecture={openLecture} onChange={refresh} refreshKey={refreshKey}/>}
          {page === 'lecture-detail' && selectedLecture && <LectureDetail lecture={selectedLecture} faculty={faculty} onBack={() => { setSelectedLecture(null); setPage('lectures') }} onChange={refresh}/>}
          {page === 'live' && <LiveClasses faculty={faculty} onChange={refresh} refreshKey={refreshKey}/>}
          {page === 'notifications' && <Notifications refreshKey={refreshKey}/>}
        </div>
      </main>
    </div>
  )
}

function PageHeading({ kicker, title, description, action }) {
  return <div className="page-heading"><div><div className="eyebrow">{kicker}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>
}

function useLoad(url, key = '') {
  const [data, setData] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  useEffect(() => { let active = true; setLoading(true); api.get(url).then(({ data: result }) => { if (active) setData(result) }).catch((err) => { if (active) setError(errorMessage(err)) }).finally(() => { if (active) setLoading(false) }); return () => { active = false } }, [url, key])
  return { data, loading, error, setData }
}

function Overview({ user, faculty, onNavigate, onOpenLecture, refreshKey }) {
  const { data: stats } = useLoad('/dashboard/', refreshKey)
  const { data: lecturesData } = useLoad('/lectures/', refreshKey)
  const lectures = unwrapList(lecturesData)
  const { data: liveData } = useLoad('/live-classes/', refreshKey)
  const upcoming = unwrapList(liveData).slice(0, 3)
  return <>
    <PageHeading kicker="YOUR CLASSROOM" title={`Good ${new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, ${(user.full_name || user.username).split(' ')[0]}.`} description={faculty ? 'Manage your subjects, share lectures and keep students informed.' : 'Pick up where you left off. Your lectures and class updates are all here.'} action={<span className="date-chip">{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' })}</span>}/>
    <section className="stat-grid">
      <StatCard label="Subjects" value={stats?.subjects ?? '—'} detail={faculty ? 'Assigned to you' : 'You are enrolled in'} icon={<BookOpen/>}/>
      <StatCard label="Lectures" value={stats?.lectures ?? '—'} detail="Available recordings" icon={<GraduationCap/>}/>
      <StatCard label="Summaries ready" value={stats?.summaries_ready ?? '—'} detail="Available in Lite Mode" icon={<Activity/>}/>
      <StatCard label="Upcoming classes" value={stats?.upcoming_live_classes ?? '—'} detail="Scheduled sessions" icon={<CalendarDays/>}/>
    </section>
    <div className="overview-grid">
      <section className="surface-panel">
        <div className="panel-heading"><div><h2>Recent lectures</h2><p>Continue with a recording or open its summary.</p></div><button className="text-button" onClick={() => onNavigate('lectures')}>View all <ChevronRight size={15}/></button></div>
        {lectures.length ? lectures.slice(0, 4).map((lecture) => <LectureRow key={lecture.id} lecture={lecture} onClick={() => onOpenLecture(lecture)}/>) : <EmptyState title="No lectures yet" message={faculty ? 'Upload your first recorded lecture from the Lectures section.' : 'Enroll in a subject to see its recorded lectures here.'}/>}
      </section>
      <section className="surface-panel upcoming-panel">
        <div className="panel-heading"><div><h2>Upcoming live classes</h2><p>Join through your scheduled class link.</p></div><button className="icon-button" onClick={() => onNavigate('live')}><ChevronRight size={18}/></button></div>
        {upcoming.length ? upcoming.map((item) => <div className="upcoming-item" key={item.id}><div className="calendar-icon"><CalendarDays size={18}/></div><div className="upcoming-info"><b>{item.title}</b><span>{item.subject_name}</span><small>{new Date(item.starts_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</small></div><a href={item.meeting_url} target="_blank" rel="noreferrer" className="join-link">Join</a></div>) : <EmptyState title="No upcoming sessions" message="Scheduled classes will appear here."/>}
        <div className="lite-banner"><div className="lite-icon"><Activity size={18}/></div><div><b>Need to save data?</b><p>Open a lecture and switch to Lite Mode to read its summary.</p></div></div>
      </section>
    </div>
  </>
}

function StatCard({ label, value, detail, icon }) { return <div className="stat-card"><div className="stat-icon">{icon}</div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{detail}</div></div> }
function EmptyState({ title, message }) { return <div className="empty-state"><div className="empty-icon"><BookOpen size={20}/></div><b>{title}</b><p>{message}</p></div> }
function LectureRow({ lecture, onClick }) { return <button className="lecture-row" onClick={onClick}><div className="lecture-thumb"><FilmIcon/></div><div className="lecture-row-info"><b>{lecture.title}</b><span>{lecture.subject_name} {lecture.topic ? `· ${lecture.topic}` : ''}</span><small>Added {new Date(lecture.created_at).toLocaleDateString('en-IN')}</small></div><div className="lecture-row-status"><StatusPill status={lecture.summary_status}/><ChevronRight size={17}/></div></button> }
function FilmIcon() { return <Film size={20}/> }

function Subjects({ faculty, onChange, refreshKey }) {
  const { data, loading, error } = useLoad(faculty ? '/subjects/mine/' : '/subjects/', refreshKey)
  const subjects = unwrapList(data)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', code: '', description: '' })
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  async function create(event) { event.preventDefault(); setBusy(true); setNotice(''); try { await api.post('/subjects/', form); setShowForm(false); setForm({ name: '', code: '', description: '' }); onChange(); setNotice('Subject created.') } catch (err) { setNotice(errorMessage(err)) } finally { setBusy(false) } }
  async function enroll(id) { setNotice(''); try { await api.post(`/subjects/${id}/enroll/`); setNotice('You are enrolled in this subject.'); onChange() } catch (err) { setNotice(errorMessage(err)) } }
  return <>
    <PageHeading kicker="LEARNING SPACE" title="Subjects" description={faculty ? 'Create and manage the subjects you teach.' : 'Find the subjects offered by your faculty and enroll to access lectures.'} action={faculty && <button className="primary-button" onClick={() => setShowForm(true)}><Plus size={17}/> New subject</button>}/>
    {notice && <div className="notice-box">{notice}</div>}{error && <div className="error-box">{error}</div>}
    {loading ? <Loading/> : <div className="subject-grid">{subjects.map((subject) => <article className="subject-card" key={subject.id}><div className="subject-card-top"><span className="subject-code">{subject.code}</span><span className="subject-count">{subject.lecture_count ?? 0} lectures</span></div><h3>{subject.name}</h3><p>{subject.description || 'Subject resources and recorded lectures.'}</p><div className="subject-card-footer"><div className="faculty-label"><div className="mini-avatar">{subject.faculty_name?.slice(0,1)}</div><span>{subject.faculty_name}</span></div>{faculty ? <span className="enrolled-label">Your subject</span> : subject.is_enrolled ? <span className="enrolled-label">Enrolled</span> : <button className="outline-button small-button" onClick={() => enroll(subject.id)}>Enroll</button>}</div></article>)}{!subjects.length && <EmptyState title="No subjects found" message="Subjects created by faculty will appear here."/>}</div>}
    {showForm && <Modal title="Create a subject" onClose={() => setShowForm(false)}><form className="form-stack" onSubmit={create}><label>Subject name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Subject code<input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} placeholder="e.g. CSE101"/></label><label>Description<textarea rows="3" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><button className="primary-button full-width" disabled={busy}>{busy ? 'Creating…' : 'Create subject'}</button></form></Modal>}
  </>
}

function Lectures({ faculty, onOpenLecture, onChange, refreshKey }) {
  const { data, loading, error } = useLoad('/lectures/', refreshKey)
  const { data: subjectData } = useLoad('/subjects/mine/', refreshKey)
  const lectures = unwrapList(data); const subjects = unwrapList(subjectData)
  const [showUpload, setShowUpload] = useState(false)
  const [form, setForm] = useState({ subject: '', title: '', topic: '', description: '', video: null })
  const [busy, setBusy] = useState(false); const [notice, setNotice] = useState(''); const [search, setSearch] = useState('')
  async function upload(event) { event.preventDefault(); if (!form.video) { setNotice('Choose a lecture video first.'); return } if (import.meta.env.VITE_FREE_TIER_MODE === 'true' && form.video.size > 25 * 1024 * 1024) { setNotice('This free demo accepts lecture videos up to 25 MB. Compress the video and try again.'); return } setBusy(true); setNotice('')
    const body = new FormData(); Object.entries(form).forEach(([key, value]) => value !== null && value !== '' && body.append(key, value))
    try {
      const { data: created } = await api.post('/lectures/', body, { timeout: 0 })
      setShowUpload(false)
      setForm({ subject: '', title: '', topic: '', description: '', video: null })
      if (import.meta.env.VITE_FREE_TIER_MODE === 'true') {
        setNotice('Lecture uploaded. Generating the Lite Mode transcript and summary…')
        try {
          await api.post(`/lectures/${created.id}/generate_summary/`, {}, { timeout: 110000 })
          setNotice('Lecture uploaded and Lite Mode summary generated successfully. Open the lecture to review it.')
        } catch (summaryError) {
          setNotice(`Lecture uploaded, but summary generation needs attention: ${errorMessage(summaryError)}`)
        }
        onChange()
      } else {
        setNotice('Lecture uploaded. Adaptive video processing and Whisper summary generation have been queued.')
        onChange()
      }
    } catch (err) { setNotice(errorMessage(err)) } finally { setBusy(false) }
  }
  const filtered = lectures.filter((l) => `${l.title} ${l.topic} ${l.subject_name}`.toLowerCase().includes(search.toLowerCase()))
  return <>
    <PageHeading kicker="RECORDED LEARNING" title="Lectures" description={faculty ? (import.meta.env.VITE_FREE_TIER_MODE === 'true' ? 'Upload a recording for enrolled students and generate a text summary.' : 'Upload a recording and let the platform prepare adaptive playback and a text summary.') : 'Watch your recorded lectures or read the summary in Lite Mode.'} action={faculty && <button className="primary-button" onClick={() => setShowUpload(true)}><UploadCloud size={17}/> Upload lecture</button>}/>
    <div className="list-toolbar"><div className="search-box"><Search size={16}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search lectures, topics or subjects"/></div><span className="muted small">{filtered.length} lecture{filtered.length === 1 ? '' : 's'}</span></div>
    {notice && <div className="notice-box">{notice}</div>}{error && <div className="error-box">{error}</div>}
    {loading ? <Loading/> : <div className="lecture-grid">{filtered.map((lecture) => <article className="lecture-card" key={lecture.id} onClick={() => onOpenLecture(lecture)}><div className="lecture-card-art"><div className="art-play"><ChevronRight size={22}/></div><span>{lecture.subject_code}</span></div><div className="lecture-card-content"><div className="lecture-card-meta"><span>{lecture.subject_name}</span><StatusPill status={lecture.summary_status}/></div><h3>{lecture.title}</h3><p>{lecture.topic || lecture.description || 'Recorded lecture'}</p><div className="lecture-card-bottom"><span>{new Date(lecture.created_at).toLocaleDateString('en-IN')}</span><span>Open lecture <ChevronRight size={14}/></span></div></div></article>)}{!filtered.length && <EmptyState title="No lectures available" message={faculty ? 'Upload your first lecture recording to get started.' : 'Enroll in a subject to access its lectures.'}/>}</div>}
    {showUpload && <Modal title="Upload a recorded lecture" onClose={() => setShowUpload(false)}><form className="form-stack" onSubmit={upload}><label>Subject<select required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}><option value="">Select a subject</option>{subjects.map((s) => <option value={s.id} key={s.id}>{s.code} — {s.name}</option>)}</select></label><label>Lecture title<input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}/></label><label>Topic<input value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}/></label><label>Description<textarea rows="2" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label className="file-drop"><UploadCloud size={24}/><b>{form.video?.name || 'Choose lecture video'}</b><span>{import.meta.env.VITE_FREE_TIER_MODE === 'true' ? 'MP4 or WEBM · up to 25 MB on free cloud hosting' : 'MP4, MOV, MKV, WEBM or AVI · maximum upload size configured by administrator'}</span><input type="file" accept={import.meta.env.VITE_FREE_TIER_MODE === 'true' ? 'video/mp4,video/webm,.mp4,.webm' : 'video/*,.mkv'} required onChange={(e) => setForm({ ...form, video: e.target.files?.[0] || null })}/></label><div className="hint-box">{import.meta.env.VITE_FREE_TIER_MODE === 'true' ? 'Free cloud demo: the original video is stored privately, then Whisper transcription is generated through the free-tier transcription API and summarized with TextRank. Uploads are limited to 25 MB.' : 'After upload, FFmpeg prepares adaptive video qualities and Whisper generates a transcript. TextRank then creates the Lite Mode summary. These steps run in the background.'}</div><button className="primary-button full-width" disabled={busy}>{busy ? 'Uploading… please keep this page open' : 'Upload and process lecture'}</button></form></Modal>}
  </>
}

function LectureDetail({ lecture: initialLecture, faculty, onBack }) {
  const [lecture, setLecture] = useState(initialLecture)
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState('summary')
  const [refresh, setRefresh] = useState(0)
  useEffect(() => {
    let active = true
    let timer
    const load = () => api.get(`/lectures/${lecture.id}/`).then(({ data }) => {
      if (!active) return
      setLecture(data)
      if (['ready', 'failed'].includes(data.summary_status) && ['ready', 'failed', 'skipped'].includes(data.hls_status)) {
        if (timer) window.clearInterval(timer)
      }
    }).catch((err) => { if (active) setNotice(errorMessage(err)) })
    load()
    timer = window.setInterval(load, 5000)
    return () => { active = false; if (timer) window.clearInterval(timer) }
  }, [lecture.id, refresh])
  async function regenerate() {
    setBusy(true); setNotice('')
    try {
      if (import.meta.env.VITE_FREE_TIER_MODE === 'true') {
        await api.post(`/lectures/${lecture.id}/generate_summary/`, {}, { timeout: 110000 })
        setNotice('Lite Mode summary generated successfully.')
      } else {
        await api.post(`/lectures/${lecture.id}/regenerate_summary/`)
        setNotice('Summary generation has been queued. Refresh this page after processing finishes.')
      }
      setRefresh((v) => v + 1)
    }
    catch (err) { setNotice(errorMessage(err)) }
    finally { setBusy(false) }
  }
  return <>
    <button className="back-button" onClick={onBack}>← Back to lectures</button>
    <PageHeading kicker={`${lecture.subject_code} · ${lecture.subject_name}`} title={lecture.title} description={lecture.topic || lecture.description || 'Recorded class and learning resources.'}/>
    {notice && <div className="notice-box">{notice}</div>}
    <div className="detail-layout"><div className="detail-main"><VideoPlayer hlsUrl={lecture.hls_url} videoUrl={lecture.video_url} title={lecture.title}/>
      <div className="processing-row"><div><b>{lecture.hls_status === 'skipped' ? 'Original video' : 'Adaptive video'}</b><span>{lecture.hls_status === 'skipped' ? 'HLS processing is disabled on free hosting' : 'FFmpeg processing'}</span></div><StatusPill status={lecture.hls_status}/><div className="processing-divider"/><div><b>Lecture summary</b><span>Whisper + TextRank</span></div><StatusPill status={lecture.summary_status}/></div>
      <section className="surface-panel discussion-panel"><div className="tab-bar"><button className={tab === 'summary' ? 'active' : ''} onClick={() => setTab('summary')}>Lite Mode summary</button><button className={tab === 'transcript' ? 'active' : ''} onClick={() => setTab('transcript')}>Full transcript</button></div>
        {tab === 'summary' && <div className="reading-pane">{lecture.summary_status === 'ready' ? <><div className="reading-meta"><span className="lite-label">LITE MODE</span><span>{lecture.summary_word_count} words</span><span>{lecture.transcription_language ? `Detected language: ${lecture.transcription_language}` : ''}</span></div><p className="summary-text">{lecture.summary}</p></> : lecture.summary_status === 'failed' ? <div className="error-box">Summary could not be generated: {lecture.summary_error || 'Unknown processing error.'}</div> : <div className="processing-state"><Activity size={24}/><b>{lecture.summary_status === 'processing' ? 'Generating your lecture summary' : 'Summary is waiting to be processed'}</b><p>The recording is transcribed with Whisper and summarized with the TextRank method.</p></div>}{faculty && ['failed', 'waiting'].includes(lecture.summary_status) && <button className="outline-button" onClick={regenerate} disabled={busy}>{busy ? 'Generating…' : lecture.summary_status === 'failed' ? 'Retry summary generation' : 'Generate Lite Mode summary'}</button>}</div>}
        {tab === 'transcript' && <div className="reading-pane transcript-pane">{lecture.transcript || <div className="processing-state"><p>The full transcript will appear here after speech-to-text processing finishes.</p></div>}</div>}
      </section>
    </div><aside className="detail-aside"><section className="surface-panel info-panel"><h3>Lecture information</h3><InfoLine label="Subject" value={`${lecture.subject_code} — ${lecture.subject_name}`}/><InfoLine label="Faculty" value={lecture.faculty_name}/><InfoLine label="Uploaded" value={new Date(lecture.created_at).toLocaleDateString('en-IN')}/><InfoLine label="Topic" value={lecture.topic || '—'}/></section><section className="lite-aside-card"><div className="lite-icon"><Activity size={18}/></div><h3>Lite Mode</h3><p>Read the main points of this lecture when streaming video is difficult or data is limited.</p><button className="light-button" onClick={() => { setTab('summary'); document.querySelector('.discussion-panel')?.scrollIntoView({ behavior: 'smooth' }) }}>Read summary</button></section><section className="surface-panel info-panel"><h3>Doubts and Q&amp;A</h3><p className="muted small">The per-lecture discussion module is planned for Sprint IV. Sprint I–III focus on the lecture platform, live-class links and automated summaries.</p></section></aside></div>
  </>
}

function InfoLine({ label, value }) { return <div className="info-line"><span>{label}</span><b>{value || '—'}</b></div> }

function LiveClasses({ faculty, onChange, refreshKey }) {
  const { data, loading, error } = useLoad('/live-classes/', refreshKey)
  const { data: subjectData } = useLoad('/subjects/mine/', refreshKey)
  const sessions = unwrapList(data); const subjects = unwrapList(subjectData)
  const [showForm, setShowForm] = useState(false); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({ subject: '', title: '', description: '', starts_at: '', meeting_url: '' })
  async function create(event) { event.preventDefault(); setBusy(true); setNotice(''); try { await api.post('/live-classes/', { ...form, starts_at: new Date(form.starts_at).toISOString() }); setShowForm(false); setForm({ subject: '', title: '', description: '', starts_at: '', meeting_url: '' }); setNotice('Live class scheduled. Enrolled students have received an in-app notification.'); onChange() } catch (err) { setNotice(errorMessage(err)) } finally { setBusy(false) } }
  return <>
    <PageHeading kicker="TIMETABLE" title="Live classes" description={faculty ? 'Schedule a session and notify students enrolled in the subject.' : 'Your upcoming Google Meet and Zoom sessions.'} action={faculty && <button className="primary-button" onClick={() => setShowForm(true)}><Plus size={17}/> Schedule class</button>}/>
    {notice && <div className="notice-box">{notice}</div>}{error && <div className="error-box">{error}</div>}
    {loading ? <Loading/> : <div className="live-list">{sessions.map((item) => <article className="live-card" key={item.id}><div className="live-date"><b>{new Date(item.starts_at).toLocaleDateString('en-IN', { day: '2-digit' })}</b><span>{new Date(item.starts_at).toLocaleDateString('en-IN', { month: 'short' })}</span></div><div className="live-info"><span>{item.subject_code} · {item.subject_name}</span><h3>{item.title}</h3><p>{item.description || `Scheduled by ${item.faculty_name}`}</p><small>{new Date(item.starts_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</small></div><a className="primary-button" href={item.meeting_url} target="_blank" rel="noreferrer">Open class <ChevronRight size={16}/></a></article>)}{!sessions.length && <EmptyState title="No scheduled classes" message="Your upcoming Google Meet or Zoom sessions will appear here."/>}</div>}
    {showForm && <Modal title="Schedule a live class" onClose={() => setShowForm(false)}><form className="form-stack" onSubmit={create}><label>Subject<select required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}><option value="">Select a subject</option>{subjects.map((s) => <option value={s.id} key={s.id}>{s.code} — {s.name}</option>)}</select></label><label>Class title<input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}/></label><label>Description<textarea rows="2" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Date and time<input required type="datetime-local" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })}/></label><label>Google Meet / Zoom link<input required type="url" placeholder="https://meet.google.com/..." value={form.meeting_url} onChange={(e) => setForm({ ...form, meeting_url: e.target.value })}/></label><div className="hint-box">Create the meeting in Google Meet or Zoom first, then paste its joining link here. Students enrolled in this subject will receive an in-app notification.</div><button className="primary-button full-width" disabled={busy}>{busy ? 'Scheduling…' : 'Schedule and notify students'}</button></form></Modal>}
  </>
}

function Notifications({ refreshKey }) {
  const { data, loading, error } = useLoad('/notifications/', refreshKey)
  const [items, setItems] = useState([])
  useEffect(() => setItems(unwrapList(data)), [data])
  async function markRead(id) { await api.post(`/notifications/${id}/mark_read/`); setItems((old) => old.map((n) => n.id === id ? { ...n, is_read: true } : n)) }
  async function markAll() { await api.post('/notifications/mark_all_read/'); setItems((old) => old.map((n) => ({ ...n, is_read: true }))) }
  return <><PageHeading kicker="UPDATES" title="Notifications" description="Class schedule updates and activity from your subjects." action={<button className="outline-button" onClick={markAll}>Mark all as read</button>}/>{error && <div className="error-box">{error}</div>}{loading ? <Loading/> : <div className="notification-list">{items.map((item) => <article className={`notification-item ${item.is_read ? '' : 'unread'}`} key={item.id}><div className="notification-icon"><Bell size={18}/></div><div className="notification-copy"><b>{item.title}</b><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString('en-IN')}</small></div>{!item.is_read && <button className="text-button" onClick={() => markRead(item.id)}>Mark read</button>}</article>)}{!items.length && <EmptyState title="You are all caught up" message="New class notifications will appear here."/>}</div>}</>
}

function Loading() { return <div className="loading-line"><span/>Loading classroom data…</div> }

export default App
