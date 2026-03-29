import { useState, useRef } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import type { DragEndEvent, DragOverEvent, DragStartEvent, UniqueIdentifier } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { KanbanColumn } from './KanbanColumn';
import { TicketCard } from './TicketCard';
import { TicketForm } from './TicketForm';
import { TicketDetail } from './TicketDetail';
import { useApp } from '../context/AppContext';
import type { Ticket, KanbanColumn as ColType } from '../types';

const COLUMNS: ColType[] = ['tickets', 'inprogress', 'completed'];

// Which column transitions are permitted
const ALLOWED_TO: Partial<Record<ColType, ColType[]>> = {
  tickets:   ['inprogress'],
  inprogress: ['completed'],
};

function getTargetColumn(overId: UniqueIdentifier, tickets: Ticket[]): ColType | undefined {
  if (typeof overId === 'string' && (COLUMNS as string[]).includes(overId)) {
    return overId as ColType;
  }
  return tickets.find(t => t.id === overId)?.column;
}

export function KanbanBoard() {
  const { tickets, setTickets } = useApp();

  const [activeTicket,  setActiveTicket]  = useState<Ticket | null>(null);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);
  const [isCreating,    setIsCreating]    = useState(false);
  const [viewingTicket, setViewingTicket] = useState<Ticket | null>(null);

  // Track the column the ticket started in so we can detect a column change on drag-end
  const dragStartColumn = useRef<ColType | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  /* ------------------------------------------------------------------ */
  /* Column helpers                                                       */
  /* ------------------------------------------------------------------ */

  function openTicketsFor(col: ColType): Ticket[] {
    return tickets
      .filter(t => t.column === col && t.status !== 'canceled')
      .sort((a, b) => a.order - b.order);
  }

  function canceledTickets(): Ticket[] {
    return tickets
      .filter(t => t.column === 'tickets' && t.status === 'canceled')
      .sort((a, b) => a.order - b.order);
  }

  /* ------------------------------------------------------------------ */
  /* Drag handlers                                                        */
  /* ------------------------------------------------------------------ */

  function handleDragStart({ active }: DragStartEvent) {
    const t = tickets.find(t => t.id === active.id) ?? null;
    setActiveTicket(t);
    dragStartColumn.current = t?.column ?? null;
  }

  function handleDragOver({ active, over }: DragOverEvent) {
    if (!over) return;
    const activeTicketData = tickets.find(t => t.id === active.id);
    if (!activeTicketData) return;

    const targetCol = getTargetColumn(over.id, tickets);
    if (!targetCol || targetCol === activeTicketData.column) return;

    // Enforce direction rules
    const allowed = ALLOWED_TO[activeTicketData.column];
    if (!allowed?.includes(targetCol)) return;

    setTickets(prev => {
      const colTickets = prev.filter(t => t.column === targetCol).sort((a, b) => a.order - b.order);
      const newOrder = colTickets.length > 0 ? Math.max(...colTickets.map(t => t.order)) + 1 : 0;
      return prev.map(t => t.id === active.id ? { ...t, column: targetCol, order: newOrder } : t);
    });
  }

  function handleDragEnd({ active, over }: DragEndEvent) {
    setActiveTicket(null);
    const originalColumn = dragStartColumn.current;
    dragStartColumn.current = null;

    const currentTicket = tickets.find(t => t.id === active.id);
    if (!currentTicket || !originalColumn) return;

    // Column changed — apply automatic status updates and prompt to edit
    if (currentTicket.column !== originalColumn) {
      const updates: Partial<Ticket> = {};

      if (currentTicket.column === 'inprogress') {
        updates.status = currentTicket.status === 'canceled' ? 'in-progress' : 'in-progress';
        if (!currentTicket.assignedDate) {
          updates.assignedDate = today();
        }
      } else if (currentTicket.column === 'completed') {
        updates.status = 'completed';
        if (!currentTicket.closedDate) updates.closedDate = today();
      }

      const updatedTicket = { ...currentTicket, ...updates };
      setTickets(prev => prev.map(t => t.id === active.id ? updatedTicket : t));
      setEditingTicket(updatedTicket);
      return;
    }

    // Same column — reorder
    if (!over || active.id === over.id) return;
    const overTicket = tickets.find(t => t.id === over.id);
    if (!overTicket || currentTicket.column !== overTicket.column) return;

    setTickets(prev => {
      const col = currentTicket.column;
      const colTickets = prev.filter(t => t.column === col).sort((a, b) => a.order - b.order);
      const oldIdx = colTickets.findIndex(t => t.id === active.id);
      const newIdx = colTickets.findIndex(t => t.id === over.id);
      if (oldIdx < 0 || newIdx < 0) return prev;
      const reordered = arrayMove(colTickets, oldIdx, newIdx).map((t, i) => ({ ...t, order: i }));
      return [...prev.filter(t => t.column !== col), ...reordered];
    });
  }

  /* ------------------------------------------------------------------ */
  /* CRUD handlers                                                        */
  /* ------------------------------------------------------------------ */

  function handleCreate(newTicket: Ticket) {
    setTickets(prev => {
      // Bump existing tickets' orders and prepend new ticket at order 0
      const colTickets = prev.filter(t => t.column === 'tickets').map(t => ({ ...t, order: t.order + 1 }));
      return [...prev.filter(t => t.column !== 'tickets'), { ...newTicket, order: 0 }, ...colTickets];
    });
    setIsCreating(false);
  }

  function handleEditSave(updated: Ticket) {
    setTickets(prev => prev.map(t => t.id === updated.id ? updated : t));
    setEditingTicket(null);
    // Keep detail panel in sync
    if (viewingTicket?.id === updated.id) setViewingTicket(updated);
  }

  function handleCancel(ticket: Ticket) {
    const updated: Ticket = {
      ...ticket,
      status: 'canceled',
      column: 'tickets',
      closedDate: ticket.closedDate ?? today(),
    };
    setTickets(prev => prev.map(t => t.id === ticket.id ? updated : t));
    // If we were viewing this ticket, update the view
    if (viewingTicket?.id === ticket.id) setViewingTicket(updated);
  }

  function handleOpenTicket(ticket: Ticket) {
    // Sync to latest version from state
    const latest = tickets.find(t => t.id === ticket.id) ?? ticket;
    setViewingTicket(latest);
  }

  /* ------------------------------------------------------------------ */
  /* Render                                                               */
  /* ------------------------------------------------------------------ */

  // Keep viewingTicket fresh if the underlying ticket changes
  const liveViewingTicket = viewingTicket
    ? (tickets.find(t => t.id === viewingTicket.id) ?? viewingTicket)
    : null;

  return (
    <div className={`kanban-wrapper${liveViewingTicket ? ' has-detail' : ''}`}>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="kanban-board">
          {COLUMNS.map(col => (
            <KanbanColumn
              key={col}
              column={col}
              openTickets={openTicketsFor(col)}
              canceledTickets={col === 'tickets' ? canceledTickets() : undefined}
              onOpenTicket={handleOpenTicket}
              onCancelTicket={handleCancel}
              onCreateTicket={col === 'tickets' ? () => setIsCreating(true) : undefined}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTicket && (
            <TicketCard ticket={activeTicket} onOpen={() => {}} isDragOverlay />
          )}
        </DragOverlay>
      </DndContext>

      {/* Create modal */}
      {isCreating && (
        <TicketForm onSave={handleCreate} onCancel={() => setIsCreating(false)} />
      )}

      {/* Edit modal */}
      {editingTicket && (
        <TicketForm
          ticket={editingTicket}
          onSave={handleEditSave}
          onCancel={() => setEditingTicket(null)}
        />
      )}

      {/* Detail panel */}
      {liveViewingTicket && (
        <TicketDetail
          ticket={liveViewingTicket}
          onEdit={t => { setEditingTicket(t); }}
          onClose={() => setViewingTicket(null)}
        />
      )}
    </div>
  );
}

function today() {
  return new Date().toISOString().split('T')[0];
}
