import { format, isSameDay, isSameYear, isYesterday } from "date-fns";
import { uk } from "date-fns/locale";

export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Детермінований колір заглушки аватара за id користувача — той самий колір щоразу,
// без запиту на сервер чи збереження вибору.
const AVATAR_CLASSES = [
  "bg-signal-500 text-ink-950",
  "bg-moss-500 text-ink-950",
  "bg-sky-500 text-white",
  "bg-violet-500 text-white",
  "bg-rose-500 text-white",
  "bg-amber-500 text-ink-950",
  "bg-teal-500 text-white",
  "bg-fuchsia-500 text-white",
];

export function getAvatarClass(id: number): string {
  return AVATAR_CLASSES[Math.abs(id) % AVATAR_CLASSES.length];
}

/** Час у списку діалогів: "щойно" / "12:45" сьогодні / "учора" / коротка дата. */
export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMinutes = (now.getTime() - date.getTime()) / 60_000;

  if (diffMinutes < 1) return "щойно";
  if (diffMinutes < 60) return `${Math.floor(diffMinutes)} хв`;
  if (isSameDay(date, now)) return format(date, "HH:mm");
  if (isYesterday(date)) return "учора";
  if (isSameYear(date, now)) return format(date, "d MMM", { locale: uk });
  return format(date, "d MMM yyyy", { locale: uk });
}

/** Час під бульбашкою повідомлення. */
export function formatMessageTime(iso: string): string {
  return format(new Date(iso), "HH:mm");
}

/** Заголовок-розділювач дня в історії повідомлень. */
export function formatDayDivider(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  if (isSameDay(date, now)) return "Сьогодні";
  if (isYesterday(date)) return "Учора";
  if (isSameYear(date, now)) return format(date, "d MMMM", { locale: uk });
  return format(date, "d MMMM yyyy", { locale: uk });
}

export function formatLastSeen(iso: string | null): string {
  if (!iso) return "давно не в мережі";
  const date = new Date(iso);
  const now = new Date();
  const diffMinutes = (now.getTime() - date.getTime()) / 60_000;
  if (diffMinutes < 1) return "був(ла) щойно";
  if (diffMinutes < 60) return `був(ла) ${Math.floor(diffMinutes)} хв тому`;
  if (isSameDay(date, now)) return `був(ла) у мережі сьогодні о ${format(date, "HH:mm")}`;
  if (isYesterday(date)) return `був(ла) у мережі вчора о ${format(date, "HH:mm")}`;
  return `був(ла) у мережі ${format(date, "d MMMM", { locale: uk })}`;
}
