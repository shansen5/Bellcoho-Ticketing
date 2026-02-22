import { useState } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import type { DragEndEvent, DragOverEvent, DragStartEvent } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { KanbanColumn } from './KanbanColumn';
import { KanbanCard } from './KanbanCard';
import type { KanbanCard as KanbanCardType, KanbanColumn as ColType } from '../types';

const COLUMNS: ColType[] = ['todo', 'inprogress', 'complete'];

interface Props {
  cards: KanbanCardType[];
  setCards: (cards: KanbanCardType[] | ((prev: KanbanCardType[]) => KanbanCardType[])) => void;
}

export function KanbanBoard({ cards, setCards }: Props) {
  const [activeCard, setActiveCard] = useState<KanbanCardType | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  function cardsForCol(col: ColType) {
    return cards
      .filter((c) => c.column === col)
      .sort((a, b) => a.order - b.order);
  }

  function addCard(column: ColType, title: string, description?: string) {
    const colCards = cardsForCol(column);
    const maxOrder = colCards.length > 0 ? Math.max(...colCards.map((c) => c.order)) : -1;
    const newCard: KanbanCardType = {
      id: crypto.randomUUID(),
      title,
      description,
      column,
      order: maxOrder + 1,
    };
    setCards((prev) => [...prev, newCard]);
  }

  function deleteCard(id: string) {
    setCards((prev) => prev.filter((c) => c.id !== id));
  }

  function handleDragStart(event: DragStartEvent) {
    const card = cards.find((c) => c.id === event.active.id);
    setActiveCard(card ?? null);
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    const activeCard = cards.find((c) => c.id === activeId);
    if (!activeCard) return;

    // Determine if we're over a column droppable or a card
    const overColumn = COLUMNS.includes(overId as ColType)
      ? (overId as ColType)
      : cards.find((c) => c.id === overId)?.column;

    if (!overColumn || activeCard.column === overColumn) return;

    // Move card to new column
    setCards((prev) => {
      const colCards = prev.filter((c) => c.column === overColumn).sort((a, b) => a.order - b.order);
      const newOrder = colCards.length > 0 ? Math.max(...colCards.map((c) => c.order)) + 1 : 0;
      return prev.map((c) =>
        c.id === activeId ? { ...c, column: overColumn, order: newOrder } : c
      );
    });
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveCard(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    if (activeId === overId) return;

    const activeCardData = cards.find((c) => c.id === activeId);
    const overCardData = cards.find((c) => c.id === overId);

    if (!activeCardData) return;

    // Reorder within same column
    if (overCardData && activeCardData.column === overCardData.column) {
      setCards((prev) => {
        const colCards = prev
          .filter((c) => c.column === activeCardData.column)
          .sort((a, b) => a.order - b.order);
        const oldIndex = colCards.findIndex((c) => c.id === activeId);
        const newIndex = colCards.findIndex((c) => c.id === overId);
        const reordered = arrayMove(colCards, oldIndex, newIndex).map((c, i) => ({
          ...c,
          order: i,
        }));
        const otherCards = prev.filter((c) => c.column !== activeCardData.column);
        return [...otherCards, ...reordered];
      });
    }
  }

  return (
    <div className="panel kanban-panel">
      <div className="panel-header">
        <span className="panel-title">Kanban Board</span>
      </div>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="kanban-board">
          {COLUMNS.map((col) => (
            <KanbanColumn
              key={col}
              column={col}
              cards={cardsForCol(col)}
              onAddCard={addCard}
              onDeleteCard={deleteCard}
            />
          ))}
        </div>
        <DragOverlay>
          {activeCard && (
            <KanbanCard card={activeCard} onDelete={() => {}} isDragOverlay />
          )}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
