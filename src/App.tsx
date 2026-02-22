import './styles/global.css';
import './styles/kanban.css';
import './styles/todo.css';
import './styles/notes.css';

import { KanbanBoard } from './components/KanbanBoard';
import { TodoList } from './components/TodoList';
import { NotesPanel } from './components/NotesPanel';
import { useLocalStorage } from './hooks/useLocalStorage';
import type { KanbanCard, TodoItem } from './types';

export default function App() {
  const [cards, setCards] = useLocalStorage<KanbanCard[]>('bch-kanban-cards', []);
  const [todos, setTodos] = useLocalStorage<TodoItem[]>('bch-todos', []);
  const [notes, setNotes] = useLocalStorage<string>('bch-notes', '');

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo-mark">M</div>
        <h1>
          Maintenance Ticketing
          <span className="org"> · Bellingham Cohousing</span>
        </h1>
      </header>
      <main className="app-body">
        <KanbanBoard cards={cards} setCards={setCards} />
        <TodoList todos={todos} setTodos={setTodos} />
        <NotesPanel notes={notes} setNotes={setNotes} />
      </main>
    </div>
  );
}
