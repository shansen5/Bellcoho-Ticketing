import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { KanbanCard as KanbanCardType } from '../types';

interface Props {
  card: KanbanCardType;
  onDelete: (id: string) => void;
  isDragOverlay?: boolean;
}

export function KanbanCard({ card, onDelete, isDragOverlay = false }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`kanban-card${isDragging ? ' dragging' : ''}${isDragOverlay ? ' drag-overlay' : ''}`}
    >
      <div className="card-title">{card.title}</div>
      {card.description && <div className="card-desc">{card.description}</div>}
      <button
        className="card-delete"
        onClick={(e) => {
          e.stopPropagation();
          onDelete(card.id);
        }}
        onPointerDown={(e) => e.stopPropagation()}
        title="Delete card"
        aria-label="Delete card"
      >
        ×
      </button>
    </div>
  );
}
