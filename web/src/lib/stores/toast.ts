import { writable } from 'svelte/store';

export interface Toast {
id: number;
kind: 'success' | 'error' | 'info';
message: string;
}

export const toasts = writable<Toast[]>([]);

let nextId = 1;

export function toast(kind: Toast['kind'], message: string): void {
const id = nextId++;
toasts.update((list) => [...list, { id, kind, message }]);
setTimeout(() => dismissToast(id), 6000);
}

export function dismissToast(id: number): void {
toasts.update((list) => list.filter((t) => t.id !== id));
}
