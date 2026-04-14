/* Theme Manager - Handles Light/Dark Mode Switching */

class ThemeManager {
    constructor() {
        this.htmlElement = document.documentElement;
        this.storageKey = 'theme';  // Use same key as existing code
        this.systemPreferencesKey = '(prefers-color-scheme: dark)';
        this.init();
    }

    init() {
        // Check for saved preference or system preference
        const savedTheme = this.getSavedTheme();
        const prefersDark = this.prefersColorScheme();
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        
        this.setTheme(theme);
        this.setupListeners();
        this.setupSystemPreferenceListener();
    }

    getSavedTheme() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return null;
        }
    }

    prefersColorScheme() {
        return window.matchMedia(this.systemPreferencesKey).matches;
    }

    setTheme(theme) {
        const validTheme = ['light', 'dark'].includes(theme) ? theme : 'light';
        
        if (validTheme === 'dark') {
            this.htmlElement.setAttribute('data-theme', 'dark');
            this.htmlElement.setAttribute('data-bs-theme', 'dark');
        } else {
            this.htmlElement.removeAttribute('data-theme');
            this.htmlElement.removeAttribute('data-bs-theme');
        }
        
        try {
            localStorage.setItem(this.storageKey, validTheme);
        } catch (e) {
            console.warn('Cannot save theme preference:', e);
        }
        
        this.updateThemeIcon();
        this.notifyThemeChange(validTheme);
    }

    getCurrentTheme() {
        return this.htmlElement.getAttribute('data-theme') || 'light';
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    updateThemeIcon() {
        const theme = this.getCurrentTheme();
        const themeBtn = document.getElementById('theme-btn');
        if (themeBtn) {
            const icon = themeBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('bi-sun', 'bi-moon', 'bi-sun-fill', 'bi-moon-fill');
                icon.classList.add(theme === 'dark' ? 'bi-sun' : 'bi-moon');
            }
        }
    }

    setupListeners() {
        const themeBtn = document.getElementById('theme-btn');
        if (themeBtn) {
            // Override existing onclick if present
            themeBtn.removeAttribute('onclick');
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        // Also support custom theme toggle button if it exists
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    setupSystemPreferenceListener() {
        const mediaQuery = window.matchMedia(this.systemPreferencesKey);
        try {
            // Modern API
            mediaQuery.addEventListener('change', (e) => {
                if (!this.getSavedTheme()) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        } catch (e) {
            // Fallback for older browsers
            try {
                mediaQuery.addListener((e) => {
                    if (!this.getSavedTheme()) {
                        this.setTheme(e.matches ? 'dark' : 'light');
                    }
                });
            } catch (e2) {
                console.warn('System preference listener not supported');
            }
        }
    }

    notifyThemeChange(theme) {
        const event = new CustomEvent('themeChanged', { detail: { theme } });
        document.dispatchEvent(event);
    }
}

// Initialize Theme Manager when DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    // DOM is already loaded
    window.themeManager = new ThemeManager();
}

// Listen for theme changes
document.addEventListener('themeChanged', (e) => {
    console.log('Theme changed to:', e.detail.theme);
});

