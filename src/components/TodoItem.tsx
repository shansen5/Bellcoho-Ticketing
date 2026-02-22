import type { TodoItem as TodoItemType } from '../types';

interface Props {
  item: TodoItemType;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export function TodoItem({ item, onToggle, onDelete }: Props) {
  return (
    <div className="todo-item">
      <input
        type="checkbox"
        className="todo-checkbox"
        checked={item.done}
        onChange={() => onToggle(item.id)}
        id={`todo-${item.id}`}
      />
      <label
        htmlFor={`todo-${item.id}`}
        className={`todo-text${item.done ? ' done' : ''}`}
      >
        {item.text}
      </label>
      <button
        className="todo-delete"
        onClick={() => onDelete(item.id)}
        title="Delete item"
        aria-label="Delete todo item"
      >
        ×
      </button>
    </div>
  );
}
