/**
 * SmileCare Dental Hospital - Main JavaScript
 * Features: Navbar scroll, AOS animations, toast notifications, smooth scroll
 */

/* ===== NAVBAR SCROLL EFFECT ===== */
window.addEventListener('scroll', function () {
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

/* ===== AOS (Animate On Scroll) - lightweight custom implementation ===== */
function initAOS() {
    const elements = document.querySelectorAll('[data-aos]');
    if (!elements.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const delay = el.getAttribute('data-aos-delay') || 0;
                    const animation = el.getAttribute('data-aos');

                    setTimeout(() => {
                        el.style.opacity = '1';
                        el.style.transform = 'translate(0, 0)';
                        el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
                    }, parseInt(delay));

                    observer.unobserve(el);
                }
            });
        },
        { threshold: 0.1, rootMargin: '0px 0px -60px 0px' }
    );

    elements.forEach((el) => {
        const animation = el.getAttribute('data-aos');
        el.style.opacity = '0';

        // Set initial transform based on animation type
        if (animation === 'fade-up') el.style.transform = 'translateY(30px)';
        else if (animation === 'fade-down') el.style.transform = 'translateY(-30px)';
        else if (animation === 'fade-left') el.style.transform = 'translateX(30px)';
        else if (animation === 'fade-right') el.style.transform = 'translateX(-30px)';
        else if (animation === 'zoom-in') el.style.transform = 'scale(0.9)';

        observer.observe(el);
    });
}

/* ===== TOAST NOTIFICATIONS ===== */
function showToast(message, type = 'info') {
    const container = document.getElementById('messagesContainer') || createToastContainer();

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show shadow-sm border-0`;
    alertDiv.setAttribute('role', 'alert');

    const icons = {
        success: '<i class="bi bi-check-circle-fill text-success fs-5"></i>',
        danger: '<i class="bi bi-exclamation-circle-fill text-danger fs-5"></i>',
        warning: '<i class="bi bi-exclamation-triangle-fill text-warning fs-5"></i>',
        info: '<i class="bi bi-info-circle-fill text-info fs-5"></i>',
    };

    alertDiv.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            ${icons[type] || icons.info}
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    container.appendChild(alertDiv);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'messagesContainer';
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

/* ===== AUTO-DISMISS MESSAGES ===== */
function initAutoDismiss() {
    const alerts = document.querySelectorAll('.messages-container .alert');
    alerts.forEach((alert, index) => {
        setTimeout(() => {
            if (alert.parentNode) {
                try {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                } catch (e) {
                    alert.style.display = 'none';
                }
            }
        }, 5000 + (index * 500));
    });
}

/* ===== SMOOTH SCROLL for anchor links ===== */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                const navbarHeight = document.getElementById('mainNavbar')?.offsetHeight || 72;
                const top = target.offsetTop - navbarHeight - 16;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });

    // Handle hash in URL on page load
    if (window.location.hash) {
        setTimeout(() => {
            const target = document.querySelector(window.location.hash);
            if (target) {
                const navbarHeight = document.getElementById('mainNavbar')?.offsetHeight || 72;
                const top = target.offsetTop - navbarHeight - 16;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        }, 300);
    }
}

/* ===== FORM VALIDATION HELPERS ===== */
function initFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    forms.forEach((form) => {
        form.addEventListener('submit', function (e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });
}

/* ===== COUNTER ANIMATION (for stats) ===== */
function animateCounter(el) {
    const target = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
    const suffix = el.textContent.replace(/[0-9]/g, '');
    const duration = 1500;
    const step = (target / duration) * 16;
    let current = 0;

    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = Math.floor(current) + suffix;
    }, 16);
}

function initCounters() {
    const stats = document.querySelectorAll('.hero-stat-number, .dash-stat-num');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    stats.forEach((el) => observer.observe(el));
}

/* ===== ACTIVE NAV LINK based on scroll position ===== */
function initScrollSpy() {
    const sections = document.querySelectorAll('section[id]');
    if (!sections.length) return;

    window.addEventListener('scroll', () => {
        let current = '';
        const navbarHeight = 80;

        sections.forEach((section) => {
            const sectionTop = section.offsetTop - navbarHeight;
            const sectionHeight = section.offsetHeight;
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                current = section.id;
            }
        });

        document.querySelectorAll('.navbar-nav .nav-link').forEach((link) => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href && href.includes('#' + current) && current) {
                link.classList.add('active');
            }
        });
    });
}

/* ===== CONFIRM DIALOGS ===== */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/* ===== INITIALIZE ALL ===== */
document.addEventListener('DOMContentLoaded', function () {
    initAOS();
    initAutoDismiss();
    initSmoothScroll();
    initCounters();
    initScrollSpy();

    // Tooltip initialization
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach((el) => new bootstrap.Tooltip(el));

    // Popover initialization
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach((el) => new bootstrap.Popover(el));

    console.log('SmileCare Dental - JavaScript initialized ✓');
});
