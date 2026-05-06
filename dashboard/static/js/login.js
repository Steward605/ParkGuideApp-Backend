(function() {
    function getSavedTheme() {
        try {
            return localStorage.getItem('theme') || 'light';
        } catch (error) {
            return 'light';
        }
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        }
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        try {
            localStorage.setItem('theme', newTheme);
        } catch (error) {
            // Ignore storage write errors and keep the selected theme for this page view.
        }
    }

    applyTheme(getSavedTheme());

    window.addEventListener('DOMContentLoaded', function() {
        applyTheme(getSavedTheme());

        const themeButton = document.getElementById('themeToggleButton');
        if (themeButton) {
            themeButton.addEventListener('click', toggleTheme);
        }

        const logo = document.getElementById('loginLogoImage');
        if (logo) {
            logo.addEventListener('error', function() {
                logo.classList.add('is-hidden');
            });
        }
    });
})();
