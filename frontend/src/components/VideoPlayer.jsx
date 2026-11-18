import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import { Film, Wifi } from 'lucide-react'

export default function VideoPlayer({ hlsUrl, videoUrl, title }) {
  const videoRef = useRef(null)
  const [mode, setMode] = useState('adaptive')
  const [error, setError] = useState('')

  useEffect(() => {
    const video = videoRef.current
    if (!video) return undefined
    setError('')
    let hls
    const source = mode === 'adaptive' && hlsUrl ? hlsUrl : videoUrl
    if (!source) return undefined

    if (mode === 'adaptive' && hlsUrl && Hls.isSupported()) {
      hls = new Hls({ enableWorker: true, capLevelToPlayerSize: true, maxBufferLength: 30 })
      hls.loadSource(hlsUrl)
      hls.attachMedia(video)
      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) setError('Adaptive playback is unavailable. Switch to the original video.')
      })
    } else if (mode === 'adaptive' && hlsUrl && video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = hlsUrl
    } else {
      video.src = videoUrl
    }

    return () => {
      if (hls) hls.destroy()
      video.removeAttribute('src')
      video.load()
    }
  }, [hlsUrl, videoUrl, mode])

  return (
    <div className="player-wrap">
      <div className="player-toolbar">
        <span><Film size={15} /> {title || 'Lecture recording'}</span>
        <div className="segmented">
          <button className={mode === 'adaptive' ? 'selected' : ''} onClick={() => setMode('adaptive')} disabled={!hlsUrl}>
            <Wifi size={14} /> Adaptive
          </button>
          <button className={mode === 'original' ? 'selected' : ''} onClick={() => setMode('original')}>Original</button>
        </div>
      </div>
      {error && <div className="inline-warning">{error}</div>}
      {videoUrl ? <video ref={videoRef} controls playsInline preload="metadata" className="video-element" /> : <div className="empty-player">Video file is not available.</div>}
      <p className="muted small">Adaptive playback adjusts the available video quality to the viewer's connection. Original playback is available as a fallback.</p>
    </div>
  )
}
