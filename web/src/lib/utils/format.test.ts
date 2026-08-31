import { describe, expect, it } from 'vitest';
import { collectRows, firstKey, formatValue, prettyKey, rowKeys, todayISO } from './format';

describe('prettyKey', () => {
it('humanizes snake_case and camelCase keys', () => {
expect(prettyKey('temperatura_minima')).toBe('Temperatura minima');
expect(prettyKey('tempMin')).toBe('Temp Min');
});
});

describe('formatValue', () => {
it('formats primitives', () => {
expect(formatValue(null)).toBe('—');
expect(formatValue(1.23456)).toBe('1.23');
expect(formatValue(true)).toBe('true');
expect(formatValue('plain')).toBe('plain');
});

it('truncates long objects and summarises long arrays', () => {
expect(formatValue({ a: 1 })).toBe('{"a":1}');
expect(formatValue([1, 2, 3])).toBe('1, 2, 3');
expect(formatValue([1, 2, 3, 4, 5])).toBe('[5 items]');
});
});

describe('firstKey', () => {
it('returns the first present key value', () => {
expect(firstKey({ a: null, b: 2 }, ['a', 'b'])).toBe(2);
expect(firstKey({ a: 1 }, ['z'])).toBeUndefined();
});
});

describe('collectRows', () => {
it('accepts arrays of objects directly', () => {
expect(collectRows([{ a: 1 }])).toEqual([{ a: 1 }]);
});

it('unwraps the first object array inside a payload', () => {
expect(collectRows({ meta: 'x', datos: [{ a: 1 }] })).toEqual([{ a: 1 }]);
});

it('returns empty arrays for unusable payloads', () => {
expect(collectRows({ meta: 'x' })).toEqual([]);
expect(collectRows(null)).toEqual([]);
});
});

describe('rowKeys', () => {
it('collects a capped set of column keys excluding technical ids', () => {
expect(rowKeys([{ a: 1, id: 2, b: 3 }], 5)).toEqual(['a', 'b']);
});
});

describe('todayISO', () => {
it('produces ISO dates with an optional offset', () => {
expect(todayISO(0)).toMatch(/^\d{4}-\d{2}-\d{2}$/);
expect(new Date(todayISO(-1)).getTime()).toBeLessThan(new Date(todayISO(0)).getTime());
});
});
