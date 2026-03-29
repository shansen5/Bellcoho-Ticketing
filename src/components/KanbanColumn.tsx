import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { TicketCard } from './TicketCard';
import { useCanCreateTicket } from '../context/AppContext';
import type { Ticket, KanbanColumn as ColType } from '../types';

const COLUMN_LABELS: Record<ColType, string> = {
  tickets:   'Tickets',
  inprogress: 'In Progress',
  completed: 'Completed',
};

interface Props {
  column: ColType;
  openTickets: Ticket[];
  canceledTickets?: Ticket[];   // only passed for 'tickets' column
  onOpenTicket: (ticket: Ticket) => void;
  onCancelTicket: (ticket: Ticket) => void;
  onCreateTicket?: () => void;  // only for 'tickets' column
}

export function KanbanColumn({
  column, openTickets, canceledTickets = [],
  onOpenTicket, onCancelTicket, onCreateTicket,
}: Props) {
  const canCreate = useCanCreateTicket();
  const { setNodeRef, isOver } = useDroppable({ id: column });

  const allIds = [...openTickets, ...canceledTickets].map(t => t.id);
  const totalCount = openTickets.length + canceledTickets.length;

  return (
    <div className="kanban-col">
      <div className="kanban-col-header">
        <span className={`col-dot col-${column}`} />
        <span className={`col-label col-label-${column}`}>{COLUMN_LABELS[column]}</span>
        <span className="col-count">{totalCount}</span>
        {column === 'tickets' && canCreate && onCreateTicket && (
          <button className="col-new-btn" onClick={onCreateTicket} title="New Ticket">
            + New
          </button>
        )}
      </div>

      <SortableContext items={allIds} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          className={`kanban-col-body${isOver ? ' is-over' : ''}`}
        >
          {totalCount === 0 && (
            <div className="col-empty">No tickets</div>
          )}

          {openTickets.map(ticket => (
            <TicketCard
              key={ticket.id}
              ticket={ticket}
              onOpen={onOpenTicket}
              onCancel={onCancelTicket}
            />
          ))}

          {canceledTickets.length > 0 && (
            <>
              <div className="canceled-section-header">
                <span>Canceled</span>
              </div>
              {canceledTickets.map(ticket => (
                <TicketCard
                  key={ticket.id}
                  ticket={ticket}
                  onOpen={onOpenTicket}
                  // canceled tickets can be dragged to In Progress but not canceled again
                />
              ))}
            </>
          )}
        </div>
      </SortableContext>
    </div>
  );
}
