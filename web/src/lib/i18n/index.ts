import { derived, writable } from 'svelte/store';
import { en } from './en';
import { es } from './es';

export const locales = ['en', 'es'] as const;
export type Locale = (typeof locales)[number];

const dictionaries: Record<Locale, unknown> = { en, es };
const COOKIE_NAME = 'agro_locale';

function fromCookie(): Locale {
if (typeof document === 'undefined') return 'es';
const match = document.cookie.match(/(?:^|; )agro_locale=(en|es)/);
return (match?.[1] as Locale) ?? 'es';
}

/** Current UI locale. Initialised from the agro_locale cookie when available. */
export const locale = writable<Locale>(fromCookie());

export function setLocale(l: Locale): void {
locale.set(l);
if (typeof document !== 'undefined') {
document.cookie = `${COOKIE_NAME}=${l}; path=/; max-age=31536000; samesite=lax`;
}
}

function resolve(dict: unknown, path: string): string | undefined {
let node: unknown = dict;
for (const key of path.split('.')) {
if (node == null || typeof node !== 'object') return undefined;
node = (node as Record<string, unknown>)[key];
}
return typeof node === 'string' ? node : undefined;
}

function interpolate(template: string, params?: Record<string, string | number>): string {
if (!params) return template;
return template.replace(/\{(\w+)\}/g, (_m, k: string) => String(params[k] ?? `{${k}}`));
}

/**
 * Reactive translation function: t('frostObserved.title') or
 * t('common.pollAttempts', { n: 3 }). Falls back to English and then to the key.
 */
export const t = derived(locale, ($locale) => {
return (path: string, params?: Record<string, string | number>): string => {
const raw = resolve(dictionaries[$locale], path) ?? resolve(dictionaries.en, path) ?? path;
return interpolate(raw, params);
};
});
