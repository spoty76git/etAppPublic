(function () {
    let navigationInitialized = false;
    let keydownHandler = null;

    function initKeyboardNavigationRegister() {

        const username = document.getElementById('register-username');
        const email = document.getElementById('register-email');
        const name = document.getElementById('register-name');
        const password = document.getElementById('register-password');
        const confirmPassword = document.getElementById('register-confirm-password');
        const registerButton = document.getElementById('register-button');


        // Exit if elements don't exist
        if (!username || !email || !name || !password || !confirmPassword || !registerButton) {
            return false;
        }

        // Prevent multiple initializations
        if (navigationInitialized) {
            return true;
        }

        navigationInitialized = true;

        // Array of focusable elements in order
        const focusableElements = [username, email, name, password, confirmPassword, registerButton];
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

                    // If focus is on any field except the last one, move to next field
                    if (currentFocusIndex < focusableElements.length - 2) {
                        currentFocusIndex++;
                        focusableElements[currentFocusIndex].focus();
                    }
                    // If focus is on the button, submit
                    else if (activeElement === confirmPassword || activeElement === registerButton) {
                        registerButton.click();
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

            if (initKeyboardNavigationRegister()) {
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

    // Observe DOM changes to detect when register page is loaded
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.type === 'childList' || mutation.type === 'subtree') {
                // Check if register elements are now present
                if (document.getElementById('register-username') &&
                    document.getElementById('register-email') &&
                    document.getElementById('register-name') &&
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