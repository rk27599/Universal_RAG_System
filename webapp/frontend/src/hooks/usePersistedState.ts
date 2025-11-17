/**
 * usePersistedState Hook
 * Synchronizes component state with localStorage
 */

import { useState, useEffect, useCallback, Dispatch, SetStateAction } from 'react';

type SetValue<T> = Dispatch<SetStateAction<T>>;

/**
 * Custom hook for state that persists to localStorage
 * @param key - localStorage key
 * @param defaultValue - default value if not found in localStorage
 * @returns [value, setValue] tuple like useState
 */
export function usePersistedState<T>(
  key: string,
  defaultValue: T
): [T, SetValue<T>] {
  // Initialize state from localStorage or default value
  const [value, setValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      if (item === null) {
        return defaultValue;
      }
      return JSON.parse(item) as T;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  // Update localStorage when value changes
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, value]);

  return [value, setValue];
}

/**
 * Hook for reading a persisted value without setting it
 * Useful for read-only access to localStorage
 */
export function usePersistedValue<T>(key: string, defaultValue: T): T {
  const [value] = usePersistedState(key, defaultValue);
  return value;
}

/**
 * Hook for getting and setting multiple localStorage keys as an object
 * Useful for settings management
 */
export function usePersistedSettings<T extends Record<string, any>>(
  prefix: string,
  defaultSettings: T
): [T, (settings: Partial<T>) => void, () => void] {
  const [settings, setSettings] = useState<T>(() => {
    const result = { ...defaultSettings };

    try {
      Object.keys(defaultSettings).forEach((key) => {
        const storageKey = `${prefix}.${key}`;
        const item = localStorage.getItem(storageKey);
        if (item !== null) {
          try {
            result[key as keyof T] = JSON.parse(item);
          } catch {
            // If parse fails, use default value
          }
        }
      });
    } catch (error) {
      console.warn(`Error reading persisted settings with prefix "${prefix}":`, error);
    }

    return result;
  });

  const updateSettings = useCallback((newSettings: Partial<T>) => {
    setSettings((prev) => {
      const updated = { ...prev, ...newSettings };

      // Persist each updated key
      Object.entries(newSettings).forEach(([key, value]) => {
        try {
          localStorage.setItem(`${prefix}.${key}`, JSON.stringify(value));
        } catch (error) {
          console.warn(`Error setting localStorage key "${prefix}.${key}":`, error);
        }
      });

      return updated;
    });
  }, [prefix]);

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);

    // Clear from localStorage
    Object.keys(defaultSettings).forEach((key) => {
      try {
        localStorage.removeItem(`${prefix}.${key}`);
      } catch (error) {
        console.warn(`Error removing localStorage key "${prefix}.${key}":`, error);
      }
    });
  }, [prefix, defaultSettings]);

  return [settings, updateSettings, resetSettings];
}

export default usePersistedState;
