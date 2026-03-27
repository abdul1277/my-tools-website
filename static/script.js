/* ==========================================
   HAMBURGER MENU FUNCTIONALITY
   ========================================== */
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function(e) {
            e.stopPropagation();
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking on a link
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.header')) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
    }

    // Dropdown menu functionality for mobile
    const dropdownButtons = document.querySelectorAll('.dropbtn');
    dropdownButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                const dropdown = this.parentElement;
                dropdown.classList.toggle('active');
            }
        });
    });
});

/* ==========================================
   TOOL CARDS ANIMATION ON LOAD
   ========================================== */
document.addEventListener('DOMContentLoaded', function() {
    const toolCards = document.querySelectorAll('.tool-card');
    
    toolCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
});

/* ==========================================
   FORM SUBMISSION HANDLING
   ========================================== */
document.addEventListener('submit', function(e) {
    const form = e.target;
    const button = form.querySelector('button[type="submit"]');
    
    if (button) {
        const originalText = button.textContent;
        button.textContent = '⏳ Processing...';
        button.disabled = true;
        button.classList.add('loading');

        // Re-enable button after response
        setTimeout(() => {
            if (button.disabled) {
                button.textContent = originalText;
                button.disabled = false;
                button.classList.remove('loading');
            }
        }, 30000); // 30 second timeout
    }
});

/* ==========================================
   FORM RESPONSE HANDLING
   ========================================== */
window.showResult = function(message, isError = false) {
    const resultDiv = document.getElementById('result') || createResultDiv();
    resultDiv.className = `result ${isError ? 'error' : 'success'}`;
    resultDiv.textContent = message;
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

function createResultDiv() {
    const resultDiv = document.createElement('div');
    resultDiv.id = 'result';
    const form = document.querySelector('form');
    form?.parentElement.appendChild(resultDiv) || document.querySelector('.container').appendChild(resultDiv);
    return resultDiv;
}

/* ==========================================
   SMOOTH SCROLLING
   ========================================== */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/* ==========================================
   KEYBOARD NAVIGATION
   ========================================== */
document.addEventListener('keydown', function(e) {
    // Close menu on Escape key
    if (e.key === 'Escape') {
        const hamburger = document.getElementById('hamburger');
        const navMenu = document.getElementById('nav-menu');
        if (hamburger?.classList.contains('active')) {
            hamburger.classList.remove('active');
            navMenu?.classList.remove('active');
        }
    }
});

/* ==========================================
   RESPONSIVE MENU RESIZE HANDLING
   ========================================== */
let currentWidth = window.innerWidth;
window.addEventListener('resize', function() {
    const newWidth = window.innerWidth;
    if ((currentWidth <= 768 && newWidth > 768) || (currentWidth > 768 && newWidth <= 768)) {
        const hamburger = document.getElementById('hamburger');
        const navMenu = document.getElementById('nav-menu');
        hamburger?.classList.remove('active');
        navMenu?.classList.remove('active');
    }
    currentWidth = newWidth;
});

/* ==========================================
   FORM VALIDATION
   ========================================== */
document.addEventListener('submit', function(e) {
    const form = e.target;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#ef4444';
            input.addEventListener('input', function() {
                this.style.borderColor = '';
            });
        }
    });
});

/* ==========================================
   PREFERS REDUCED MOTION
   ========================================== */
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('*').forEach(element => {
        element.style.animationDuration = '0.01ms !important';
        element.style.transitionDuration = '0.01ms !important';
    });
}

/* ==========================================
   ACCESSIBLE FOCUS MANAGEMENT
   ========================================== */
document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-nav');
    }
});

document.addEventListener('mousedown', function() {
    document.body.classList.remove('keyboard-nav');
});

/* ==========================================
   DARK MODE DETECTION
   ========================================== */
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.body.classList.add('dark-mode');
}

window.matchMedia('(prefers-color-scheme: dark)').addListener(function(e) {
    if (e.matches) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
});