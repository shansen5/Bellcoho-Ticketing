import './styles/global.css';
import './styles/kanban.css';
import './styles/tickets.css';
import './styles/modal.css';
import './styles/detail.css';

import { AppProvider, useApp } from './context/AppContext';
import { KanbanBoard } from './components/KanbanBoard';

function AppShell() {
  const { currentUser } = useApp();
  return (
    <div className="app">
      <header className="app-header">
        <div className="logo-mark">M</div>
        <h1>
          Maintenance Ticketing
          <span className="org"> · Bellingham Cohousing</span>
        </h1>
        <div className="user-badge">
          <span className="user-name">{currentUser.name}</span>
          <span className={`role-chip role-${currentUser.role}`}>{currentUser.role}</span>
        </div>
      </header>
      <main className="app-body">
        <KanbanBoard />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}
