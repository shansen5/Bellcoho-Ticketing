import { useState, useEffect, useRef } from 'react';

interface Props {
  notes: string;
  setNotes: (notes: string) => void;
}

export function NotesPanel({ notes, setNotes }: Props) {
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setNotes(e.target.value);
    setSaved(false);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setSaved(true), 800);
  }

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <div className="panel notes-panel">
      <div className="panel-header">
        <span className="panel-title">Notes</span>
      </div>
      <div className="notes-body">
        <textarea
          className="notes-textarea"
          placeholder="Freeform notes — maintenance logs, contacts, observations…"
          value={notes}
          onChange={handleChange}
        />
      </div>
      <div className="notes-footer">
        {saved && (
          <span className="notes-saved-indicator">
            <span className="dot" />
            Saved
          </span>
        )}
      </div>
    </div>
  );
}
