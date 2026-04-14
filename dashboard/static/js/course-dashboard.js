/* Course Dashboard - Search & Filter Functionality */

class CourseDashboard {
    constructor() {
        this.courseGrid = document.getElementById('courseGrid');
        this.searchInput = document.getElementById('courseSearch');
        this.filterButtons = document.querySelectorAll('.filter-button');
        this.currentFilter = 'all';
        this.init();
    }

    init() {
        if (!this.courseGrid) return;

        this.setupSearchListener();
        this.setupFilterListeners();
        this.loadCourseMetadata();
        this.setupCardAnimations();
    }

    setupSearchListener() {
        if (this.searchInput) {
            // Debounce search
            let searchTimeout;
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filterCourses();
                }, 300);
            });
        }
    }

    setupFilterListeners() {
        this.filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                this.currentFilter = button.dataset.filter;
                this.filterCourses();
            });
        });
    }

    loadCourseMetadata() {
        const cards = this.courseGrid.querySelectorAll('.course-card');
        cards.forEach(card => {
            // Extract course name from card for search
            const titleElem = card.querySelector('.course-title');
            const codeElem = card.querySelector('.course-code');
            
            if (titleElem) card.dataset.courseName = titleElem.textContent.toLowerCase();
            if (codeElem) card.dataset.courseCode = codeElem.textContent.toLowerCase();
            
            // Extract tags for filtering
            const tags = card.querySelectorAll('.course-tag');
            const tagList = Array.from(tags).map(t => t.dataset.tag || t.textContent.toLowerCase());
            card.dataset.tags = tagList.join(',');
        });
    }

    filterCourses() {
        const searchTerm = this.searchInput ? this.searchInput.value.toLowerCase() : '';
        const cards = this.courseGrid.querySelectorAll('.course-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const courseName = card.dataset.courseName || '';
            const courseCode = card.dataset.courseCode || '';
            const tags = (card.dataset.tags || '').split(',');
            
            // Check search match
            const matchSearch = 
                courseName.includes(searchTerm) || 
                courseCode.includes(searchTerm);
            
            if (!searchTerm && !matchSearch) return;

            // Check filter match
            let matchFilter = this.currentFilter === 'all';
            if (!matchFilter && this.currentFilter) {
                matchFilter = tags.includes(this.currentFilter);
            }

            const shouldShow = matchSearch && matchFilter;
            
            if (shouldShow) {
                this.showCard(card);
                visibleCount++;
            } else {
                this.hideCard(card);
            }
        });

        this.showEmptyState(visibleCount === 0);
    }

    showCard(card) {
        card.style.display = '';
        card.classList.remove('hidden');
        // Trigger animation
        setTimeout(() => card.classList.add('fade-in'), 10);
    }

    hideCard(card) {
        card.classList.remove('fade-in');
        card.classList.add('hidden');
        setTimeout(() => {
            card.style.display = 'none';
        }, 300);
    }

    showEmptyState(show) {
        let emptyState = this.courseGrid.querySelector('.empty-state');
        
        if (show && !emptyState) {
            emptyState = document.createElement('div');
            emptyState.className = 'empty-state col-12 text-center py-5';
            emptyState.innerHTML = `
                <i class="bi bi-inbox" style="font-size: 3rem; opacity: 0.5;"></i>
                <p class="mt-3" style="opacity: 0.7;">No courses found</p>
            `;
            this.courseGrid.appendChild(emptyState);
        } else if (!show && emptyState) {
            emptyState.remove();
        }
    }

    setupCardAnimations() {
        const cards = this.courseGrid.querySelectorAll('.course-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.05}s`;
        });
    }

    // Public API for external control
    search(term) {
        if (this.searchInput) {
            this.searchInput.value = term;
            this.filterCourses();
        }
    }

    filter(filterType) {
        this.filterButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.filter === filterType) {
                btn.classList.add('active');
            }
        });
        this.currentFilter = filterType;
        this.filterCourses();
    }

    reset() {
        if (this.searchInput) this.searchInput.value = '';
        this.currentFilter = 'all';
        this.filterButtons.forEach(btn => btn.classList.remove('active'));
        this.filterButtons[0]?.classList.add('active');
        this.filterCourses();
    }
}

// Initialize Course Dashboard
document.addEventListener('DOMContentLoaded', () => {
    window.courseDashboard = new CourseDashboard();
});

// Utility function to format course stats
function formatStat(value, type = 'number') {
    if (type === 'percentage') {
        return `${Math.round(value)}%`;
    }
    if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}k`;
    }
    return value.toString();
}

// Utility function to get course status badge
function getCourseStatusBadge(course) {
    const badges = [];
    
    if (course.is_entry_point) {
        badges.push('<span class="badge badge-success">Entry Point</span>');
    }
    if (course.has_prerequisites) {
        badges.push('<span class="badge badge-info">Has Prerequisites</span>');
    }
    if (course.progress_percentage !== undefined) {
        if (course.progress_percentage === 100) {
            badges.push('<span class="badge badge-success">Completed</span>');
        } else if (course.progress_percentage > 0) {
            badges.push('<span class="badge badge-warning">In Progress</span>');
        }
    }
    
    return badges.join(' ');
}

// Utility function to animate progress bars
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const target = parseFloat(bar.dataset.progress || 0);
        let current = 0;
        const increment = target / 20;
        const interval = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            bar.style.width = `${current}%`;
        }, 30);
    });
}

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    animateProgressBars();
});
