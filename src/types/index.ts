export type UserRole = 'admin' | 'maintenance' | 'resident';

export type User = {
  id: string;
  name: string;
  role: UserRole;
};

export type TicketStatus = 'open' | 'in-progress' | 'closed' | 'canceled' | 'completed';
export type TicketPriority = 'low' | 'medium' | 'high' | 'critical';
export type KanbanColumn = 'tickets' | 'inprogress' | 'completed';
export type VendorArea = 'plumbing' | 'electrical' | 'hvac' | 'heat-pump' | 'solar';

export type Ticket = {
  id: number;                     // system-generated unique integer
  openedAt: string;               // ISO datetime
  reportedBy: string;             // User ID
  description: string;
  priority: TicketPriority;
  status: TicketStatus;
  column: KanbanColumn;
  order: number;
  assignedDate?: string;          // YYYY-MM-DD
  dueDate?: string;               // YYYY-MM-DD
  closedDate?: string;            // completed/closed/canceled date, YYYY-MM-DD
  cohousignAssignee?: string;     // User ID
  vendorId?: string;
  vendorQualityAssessment?: string;
  partsReplaced?: string;
  relatedTicketIds: number[];
};

export type ToDo = {
  id: string;
  ticketId: number;
  description: string;
  openedBy: string;               // User ID
  openedAt: string;               // ISO datetime
  status: 'open' | 'closed';
  closedAt?: string;              // ISO datetime
};

export type Note = {
  id: string;
  ticketId: number;
  todoId?: string;                // if attached to a todo
  description: string;
  createdBy: string;              // User ID
  createdAt: string;              // ISO datetime
};

export type Vendor = {
  id: string;
  area: VendorArea;
  phone: string;
  names: string[];
};
