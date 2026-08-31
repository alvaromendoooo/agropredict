import { describe, expect, it } from 'vitest';
import { alertLevelColor, riskBadgeClass, riskLevel } from './risk';

describe('riskLevel', () => {
it('maps critical labels', () => {
expect(riskLevel('CRITICA')).toBe('critical');
expect(riskLevel('critical')).toBe('critical');
});

it('maps high and moderate labels', () => {
expect(riskLevel('ALTA')).toBe('high');
expect(riskLevel('MODERADA')).toBe('moderate');
});

it('maps low labels', () => {
expect(riskLevel('BAJA')).toBe('low');
expect(riskLevel('DEBIL')).toBe('low');
});

it('maps no-risk labels', () => {
expect(riskLevel('SIN_RIESGO')).toBe('none');
expect(riskLevel('NO RISK')).toBe('none');
});

it('returns unknown for empty or unrecognized labels', () => {
expect(riskLevel('')).toBe('unknown');
expect(riskLevel(null)).toBe('unknown');
expect(riskLevel('???')).toBe('unknown');
});

it('provides stable badge classes per level', () => {
expect(riskBadgeClass('CRITICA')).toContain('bg-red-100');
expect(riskBadgeClass('SIN_RIESGO')).toContain('bg-green-100');
});
});

describe('alertLevelColor', () => {
it('colors weekly alert levels on the 0-100 scale', () => {
expect(alertLevelColor(10)).toBe('bg-lime-400');
expect(alertLevelColor(60)).toBe('bg-amber-400');
expect(alertLevelColor(90)).toBe('bg-red-500');
expect(alertLevelColor('not-a-number')).toBe('bg-slate-200');
});
});
