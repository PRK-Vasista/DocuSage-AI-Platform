/**
 * Theme preference hook for DocuSage light/dark modes.
 */

import { useCallback, useEffect, useState } from 'react';
import { THEME_STORAGE_KEY } from '../config/appConfig';

/**
 * Resolve the initial theme from storage or system preference.
 *
 * @returns {'light'|'dark'} Initial theme mode.
 */
function resolveInitialTheme() {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
        return stored;
    }

    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }

    return 'light';
}

/**
 * Apply theme to the document root for CSS variable switching.
 *
 * @param {'light'|'dark'} theme - Active theme mode.
 */
function applyThemeToDocument(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

/**
 * Manage light/dark theme state with localStorage persistence.
 *
 * @returns {{theme: 'light'|'dark', isDark: boolean, toggleTheme: Function, setTheme: Function}}
 */
const useTheme = () => {
    const [theme, setThemeState] = useState(() => {
        const initial = resolveInitialTheme();
        applyThemeToDocument(initial);
        return initial;
    });

    useEffect(() => {
        applyThemeToDocument(theme);
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    }, [theme]);

    const setTheme = useCallback((nextTheme) => {
        if (nextTheme !== 'light' && nextTheme !== 'dark') {
            return;
        }
        setThemeState(nextTheme);
    }, []);

    const toggleTheme = useCallback(() => {
        setThemeState((current) => (current === 'dark' ? 'light' : 'dark'));
    }, []);

    return {
        theme,
        isDark: theme === 'dark',
        toggleTheme,
        setTheme,
    };
};

export default useTheme;
