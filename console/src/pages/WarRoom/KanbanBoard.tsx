import {
  DragDropContext,
  Droppable,
  Draggable,
  type DropResult,
} from "@hello-pangea/dnd";
import { Tooltip } from "antd";
import type { Task } from "../../api/warroom";
import styles from "./KanbanBoard.module.less";

interface KanbanBoardProps {
  tasks: Task[];
  onTaskSelect: (task: Task) => void;
  onTaskMove?: (taskId: string, newStatus: string) => void;
}

const COLUMNS = [
  { id: "pending", label: "Pending", color: "var(--pb-wr-text-secondary)" },
  { id: "claimed", label: "Claimed", color: "var(--pb-wr-accent)" },
  { id: "in_progress", label: "In Progress", color: "var(--pb-wr-status-progress)" },
  { id: "done", label: "Done", color: "var(--pb-wr-status-done)" },
  { id: "failed", label: "Failed", color: "var(--pb-wr-status-failed)" },
] as const;

function priorityClass(priority: string): string {
  if (priority === "high" || priority === "critical") return styles.cardHigh;
  if (priority === "low") return styles.cardLow;
  return styles.cardNormal;
}

function formatRelativeTime(ts: string | null): string {
  if (!ts) return "";
  try {
    const age = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(age / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  } catch {
    return "";
  }
}

function TaskCard({
  task,
  index,
  onSelect,
}: {
  task: Task;
  index: number;
  onSelect: (t: Task) => void;
}) {
  const isBlocked = task.blocked_by.length > 0;

  return (
    <Draggable draggableId={task.task_id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`${styles.card} ${priorityClass(task.priority)} ${
            snapshot.isDragging ? styles.cardDragging : ""
          } ${isBlocked ? styles.cardBlocked : ""}`}
          onClick={() => onSelect(task)}
        >
          <div className={styles.cardTitle}>{task.title}</div>
          {task.description && (
            <Tooltip title={task.description}>
              <div className={styles.cardDescription}>
                {task.description}
              </div>
            </Tooltip>
          )}
          <div className={styles.cardMeta}>
            {task.owner_name && (
              <span className={`${styles.tag} ${styles.tagOwner}`}>
                {task.owner_name}
              </span>
            )}
            {task.file_scopes.length > 0 && (
              <Tooltip
                title={task.file_scopes.join("\n")}
                overlayStyle={{ whiteSpace: "pre-wrap" }}
              >
                <span className={`${styles.tag} ${styles.tagFiles}`}>
                  {task.file_scopes.length} file
                  {task.file_scopes.length !== 1 ? "s" : ""}
                </span>
              </Tooltip>
            )}
            {isBlocked && (
              <Tooltip
                title={`Blocked by: ${task.blocked_by.join(", ")}`}
              >
                <span className={`${styles.tag} ${styles.tagBlocked}`}>
                  BLOCKED
                </span>
              </Tooltip>
            )}
            {task.priority !== "normal" && (
              <span
                className={`${styles.tag} ${
                  task.priority === "high" || task.priority === "critical"
                    ? styles.tagPriorityHigh
                    : styles.tagPriorityLow
                }`}
              >
                {task.priority.toUpperCase()}
              </span>
            )}
          </div>
          {task.progress_note && (
            <div className={styles.progressNote}>{task.progress_note}</div>
          )}
          <div className={styles.cardTimestamp}>
            {task.completed_at
              ? `Completed ${formatRelativeTime(task.completed_at)}`
              : task.claimed_at
                ? `Claimed ${formatRelativeTime(task.claimed_at)}`
                : `Created ${formatRelativeTime(task.created_at)}`}
          </div>
        </div>
      )}
    </Draggable>
  );
}

export default function KanbanBoard({
  tasks,
  onTaskSelect,
  onTaskMove,
}: KanbanBoardProps) {
  const grouped = COLUMNS.reduce(
    (acc, col) => {
      acc[col.id] = tasks.filter((t) => t.status === col.id);
      return acc;
    },
    {} as Record<string, Task[]>,
  );

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination || !onTaskMove) return;
    const newStatus = result.destination.droppableId;
    if (newStatus !== result.source.droppableId) {
      onTaskMove(result.draggableId, newStatus);
    }
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className={styles.board}>
        {COLUMNS.map((col) => (
          <div key={col.id} className={styles.column}>
            <div className={styles.columnHeader}>
              <div className={styles.columnHeaderLeft}>
                <span
                  className={styles.columnDot}
                  style={{ background: col.color }}
                />
                <span className={styles.columnTitle}>{col.label}</span>
              </div>
              <span className={styles.columnCount}>
                {grouped[col.id]?.length || 0}
              </span>
            </div>
            <Droppable droppableId={col.id}>
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`${styles.cardList} ${
                    snapshot.isDraggingOver ? styles.cardListDragOver : ""
                  }`}
                >
                  {grouped[col.id]?.length === 0 && (
                    <div className={styles.empty}>No tasks</div>
                  )}
                  {grouped[col.id]?.map((task, idx) => (
                    <TaskCard
                      key={task.task_id}
                      task={task}
                      index={idx}
                      onSelect={onTaskSelect}
                    />
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        ))}
      </div>
    </DragDropContext>
  );
}
