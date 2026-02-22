import { useState } from 'react';
import { TodoItem } from './TodoItem';
import type { TodoItem as TodoItemType } from '../types';

interface Props {
  todos: TodoItemType[];
  setTodos: (todos: TodoItemType[] | ((prev: TodoItemType[]) => TodoItemType[])) => void;
}

export function TodoList({ todos, setTodos }: Props) {
  const [input, setInput] = useState('');

  function addTodo() {
    const text = input.trim();
    if (!text) return;
    const newItem: TodoItemType = {
      id: crypto.randomUUID(),
      text,
      done: false,
    };
    setTodos((prev) => [...prev, newItem]);
    setInput('');
  }

  function toggleTodo(id: string) {
    setTodos((prev) =>
      prev.map((item) => (item.id === id ? { ...item, done: !item.done } : item))
    );
  }

  function deleteTodo(id: string) {
    setTodos((prev) => prev.filter((item) => item.id !== id));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') addTodo();
  }

  const doneCount = todos.filter((t) => t.done).length;
  const total = todos.length;
  const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;

  return (
    <div className="panel todo-panel">
      <div className="panel-header">
        <span className="panel-title">Todo List</span>
      </div>

      {total > 0 && (
        <div className="todo-progress">
          <div className="todo-progress-bar">
            <div className="todo-progress-fill" style={{ width: `${pct}%` }} />
          </div>
          <span className="todo-progress-label">{doneCount}/{total}</span>
        </div>
      )}

      <div className="todo-list">
        {todos.length === 0 && (
          <div className="todo-empty">No tasks yet</div>
        )}
        {todos.map((item) => (
          <TodoItem
            key={item.id}
            item={item}
            onToggle={toggleTodo}
            onDelete={deleteTodo}
          />
        ))}
      </div>

      <div className="todo-add-form">
        <input
          className="todo-add-input"
          type="text"
          placeholder="Add a task…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="todo-add-btn" onClick={addTodo} title="Add task">
          +
        </button>
      </div>
    </div>
  );
}
