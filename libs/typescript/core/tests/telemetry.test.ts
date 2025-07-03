import { beforeEach, describe, expect, it } from 'vitest';
import { Telemetry } from '../src/';

describe('Telemetry', () => {
  let telemetry: Telemetry;
  beforeEach(() => {
    process.env.CUA_TELEMETRY = '';
    process.env.CUA_TELEMETRY_DISABLED = '';
    telemetry = new Telemetry();
  });
  describe('telemetry.enabled', () => {
    it('should return false when CUA_TELEMETRY is off', () => {
      process.env.CUA_TELEMETRY = 'off';
      telemetry = new Telemetry();
      expect(telemetry.enabled).toBe(false);
    });

    it('should return true when CUA_TELEMETRY is not set', () => {
      process.env.CUA_TELEMETRY = '';
      telemetry = new Telemetry();
      expect(telemetry.enabled).toBe(true);
    });

    it('should return false if CUA_TELEMETRY_DISABLED is 1', () => {
      process.env.CUA_TELEMETRY_DISABLED = '1';
      telemetry = new Telemetry();
      expect(telemetry.enabled).toBe(false);
    });
  });
});
