// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { WeatherState } from '@ferret/weather';

/**
 * The weather of the game: the one file that says what the sky and the air do. A scene asks for a weather by its name (`WEATHER.active`, or `?weather=name` in the address of the
 * page), and everything reads it from there: the sky, the clouds, the sun, the haze, the wind field with its gusts, and with them the trees, the grass, the wires, the awnings,
 * the flags and the litter. To change the weather of a scene, change `active` or add a line to `presets`; no other file holds a number of the weather.
 */
export interface WeatherPreset {
  /** what it is, in words (for the logbook and the inspector) */
  description: string;
  /** a preset of `@ferret/weather` (`clear`, `fair`, `overcast` ...) and the numbers changed over it */
  base: string;
  state: Partial<WeatherState>;
  /** the hour of the day, local solar time, 0..24 (the sun follows it) */
  hour: number;
  /** the compass of the set: the sun's azimuth at its highest point is south; `sunRoll` turns the sun's path about the vertical, degrees, so the light falls along or across the street */
  sunRoll: number;
  /** how far the eye sees through the air, km (the haze) */
  visibilityKm: number;
  /** how many of the clouds are fair-weather cumulus against high thin ones, 0..1 */
  cumulus: number;
}

export const WEATHER: { active: string; presets: Record<string, WeatherPreset> } = {
  active: 'light-cloud',
  presets: {
    clear: {
      description: 'clear sky, light breeze',
      base: 'clear', state: { wind: 2.5, windDir: 70, gustiness: 0.15, cloudCover: 0.04, temperature: 24 },
      hour: 12.2, sunRoll: 0, visibilityKm: 38, cumulus: 0.2,
    },
    'light-cloud': {
      description: 'light cloud, a fresh breeze',
      base: 'fair', state: { wind: 5.5, windDir: 70, gustiness: 0.3, cloudCover: 0.32, convection: 0.35, temperature: 22 },
      hour: 15.5, sunRoll: 0, visibilityKm: 30, cumulus: 0.8,
    },
    'strong-wind': {
      description: 'strong wind, broken cloud, dust on the road',
      base: 'fair', state: { wind: 15, windDir: 60, gustiness: 0.75, cloudCover: 0.5, convection: 0.4, temperature: 21, dustiness: 0.35 },
      hour: 16.2, sunRoll: 0, visibilityKm: 22, cumulus: 0.7,
    },
    sunset: {
      description: 'clear evening, a low sun, a breeze',
      base: 'clear', state: { wind: 3.5, windDir: 70, gustiness: 0.2, cloudCover: 0.14, temperature: 19 },
      hour: 18.9, sunRoll: 0, visibilityKm: 34, cumulus: 0.3,
    },
  },
};

/** the preset asked for: `name` or the one in the address of the page, else the active one of this file */
export function weatherPreset(name?: string): { name: string; preset: WeatherPreset } {
  const n = name && WEATHER.presets[name] ? name : WEATHER.active;
  return { name: n, preset: WEATHER.presets[n] };
}
