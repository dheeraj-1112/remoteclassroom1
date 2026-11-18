import { X } from 'lucide-react'

export default function Modal({ title, onClose, children }) {
  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal-card">
        <header className="modal-header"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close"><X size={18} /></button></header>
        {children}
      </section>
    </div>
  )
}
