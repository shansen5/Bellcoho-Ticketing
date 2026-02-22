import { useState } from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { KanbanCard } from './KanbanCard';
import type { KanbanCard as KanbanCardType, KanbanColumn as ColType } from '../types';

const COLUMN_LABELS: Record<ColType, string> = {
  todo: 'To Do',
  inprogress: 'In Progress',
  complete: 'Complete',
};

interface Props {
  column: ColType;
  cards: KanbanCardType[];
  onAddCard: (column: ColType, title: string, description?: string) => void;
  onDeleteCard: (id: string) => void;
}

export function KanbanColumn({ column, cards, onAddCard, onDeleteCard }: Props) {
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');

  const { setNodeRef, isOver } = useDroppable({ id: column });

  function handleSave() {
    const t = title.trim();
    if (!t) return;
    onAddCard(column, t, desc.trim() || undefined);
    setTitle('');
    setDesc('');
    setAdding(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      setTitle('');
      setDesc('');
      setAdding(false);
    }
  }

  const cardIds = cards.map((c) => c.id);

  return (
    <div className="kanban-col">
      <div className="kanban-col-header">
        <span className={`col-dot ${column}`} />
        <span className={`col-label ${column}`}>{COLUMN_LABELS[column]}</span>
        <span className="col-count">{cards.length}</span>
      </div>

      <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          className={`kanban-col-body${isOver ? ' is-over' : ''}`}
        >
          {cards.length === 0 && !adding && (
            <div className="col-empty">Drop cards here</div>
          )}
          {cards.map((card) => (
            <KanbanCard key={card.id} card={card} onDelete={onDeleteCard} />
          ))}
        </div>
      </SortableContext>

      {adding ? (
        <div className="col-add-form">
          <textarea
            autoFocus
            placeholder="Card title (Enter to save, Shift+Enter for new line)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="col-add-form-actions">
            <button className="btn-save" onClick={handleSave}>Add Card</button>
            <button
              className="btn-cancel"
              onClick={() => {
                setTitle('');
                setDesc('');
                setAdding(false);
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="col-add-trigger">
          <button onClick={() => setAdding(true)}>
            <span style={{ fontSize: 16, lineHeight: 1 }}>+</span>
            Add card
          </button>
        </div>
      )}
    </div>
  );
}
