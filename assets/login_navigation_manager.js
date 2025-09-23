(function () {
    let navigationInitialized = false;
    let keydownHandler = null;

    function initKeyboardNavigationLogin() {

        const username = document.getElementById('login-username');
        const password = document.getElementById('login-password');
        const loginButton = document.getElementById('login-button');


        // Exit if elements don't exist
        if (!username || !password || !loginButton) {
            return false;
        }

        // Prevent multiple initializations
        if (navigationInitialized) {
            return true;
        }

        navigationInitialized = true;

        // Array of focusable elements in order
        const focusableElements = [username, password, loginButton];
        let currentFocusIndex = 0;

        // Set initial focus to username field after a short delay
        // setTimeout(() => {
        //     username.focus();
        // }, 10);
        username.focus();

        // Remove existing event listener if any
        if (keydownHandler) {
            document.removeEventListener('keydown', keydownHandler);
        }

        // Handle keydown events for navigation
        keydownHandler = function (event) {
            // Only handle navigation when one of our elements is focused
            const activeElement = document.activeElement;
            if (!focusableElements.includes(activeElement)) {
                return;
            }

            switch (event.key) {
                case 'ArrowDown':
                case 'ArrowRight':
                    event.preventDefault();
                    currentFocusIndex = (currentFocusIndex + 1) % focusableElements.length;
                    focusableElements[currentFocusIndex].focus();
                    break;

                case 'ArrowUp':
                case 'ArrowLeft':
                    event.preventDefault();
                    currentFocusIndex = (currentFocusIndex - 1 + focusableElements.length) % focusableElements.length;
                    focusableElements[currentFocusIndex].focus();
                    break;

                case 'Enter':
                    event.preventDefault();

                    // If focus is on username, move to password
                    if (activeElement === username) {
                        password.focus();
                        currentFocusIndex = 1;
                    }
                    // If focus is on password or button, submit
                    else if (activeElement === password || activeElement === loginButton) {
                        loginButton.click();
                    }
                    break;
            }
        };

        // Add keydown event listener
        document.addEventListener('keydown', keydownHandler);

        // Update focus index when elements are clicked/focused
        focusableElements.forEach((element, index) => {
            element.addEventListener('focus', function () {
                currentFocusIndex = index;
            });
        });

        return true;
    }

    // Reset navigation state when page changes
    function resetNavigation() {
        navigationInitialized = false;
        if (keydownHandler) {
            document.removeEventListener('keydown', keydownHandler);
            keydownHandler = null;
        }
    }

    // Retry mechanism for Dash's dynamic rendering
    function attemptInitialization(maxAttempts = 20, attemptInterval = 250) {
        let attempts = 0;

        function tryInit() {
            attempts++;

            if (initKeyboardNavigationLogin()) {
                return;
            }

            if (attempts < maxAttempts) {
                setTimeout(tryInit, attemptInterval);
            }
        }

        tryInit();
    }

    // Initialize on page load
    function initialize() {
        resetNavigation();
        attemptInitialization();
    }

    // Listen for both initial load and dynamic page changes
    if (document.readyState !== 'loading') {
        initialize();
    } else {
        document.addEventListener('DOMContentLoaded', initialize);
    }

    // Listen for URL changes (for SPAs)
    window.addEventListener('popstate', initialize);

    // Listen for hash changes
    window.addEventListener('hashchange', initialize);

    // Observe DOM changes to detect when login page is loaded
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.type === 'childList' || mutation.type === 'subtree') {
                // Check if login elements are now present
                if (document.getElementById('login-username') &&
                    document.getElementById('login-password') &&
                    document.getElementById('login-button') &&
                    !navigationInitialized) {
                    initialize();
                }
            }
        });
    });

    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

})();