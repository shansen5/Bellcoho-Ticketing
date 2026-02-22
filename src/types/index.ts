export type KanbanColumn = 'todo' | 'inprogress' | 'complete';

export type KanbanCard = {
  id: string;
  title: string;
  description?: string;
  column: KanbanColumn;
  order: number;
};

export type TodoItem = {
  id: string;
  text: string;
  done: boolean;
};

export type AppState = {
  cards: KanbanCard[];
  todos: TodoItem[];
  notes: string;
};
