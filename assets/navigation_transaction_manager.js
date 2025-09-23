(function () {
    // Tab ordering, auto ID assignment
    const order = [
        'tm-category',
        'tm-merchant',
        'tm-amount',
        'tm-note',
        'tm-date-left-arrow',
        'tm-date-right-arrow'
    ];

    function getFocusableElement(id) {
        if (id === 'tm-category') {
            const dropdown = document.getElementById(id);
            if (dropdown) {
                const input = dropdown.querySelector('input');
                return input || dropdown;
            }
        }
        // Handle date arrows
        if (id === 'tm-date-left-arrow') {
            return document.getElementById('tm-date-decrement');
        }
        if (id === 'tm-date-right-arrow') {
            return document.getElementById('tm-date-increment');
        }
        return document.getElementById(id);
    }

    function focusPrevious(currentId) {
        const index = order.indexOf(currentId);
        if (index > 0) {
            const prevId = order[index - 1];
            const prevElement = getFocusableElement(prevId);
            if (prevElement) prevElement.focus();
        }
    }

    function focusNext(currentId) {
        const index = order.indexOf(currentId);
        if (index < order.length - 1) {
            const nextId = order[index + 1];
            const nextElement = getFocusableElement(nextId);
            if (nextElement) nextElement.focus();
        }
    }

    // Simulate button clicks
    function clickButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.click();
        }
    }

    // Additional handlers
    function changeDateBy(days, element) {
        const dateInput = document.getElementById(element);
        if (!dateInput) return;
        const currentDate = new Date(dateInput.value);
        if (isNaN(currentDate.getTime())) return;
        currentDate.setDate(currentDate.getDate() + 1); // idk why this works but need to add 1
        const yyyy = currentDate.getFullYear();
        const mm = String(currentDate.getMonth() + 1).padStart(2, '0');
        const dd = String(currentDate.getDate() + days).padStart(2, '0');
        const formatted = `${yyyy}-${mm}-${dd}`;
        dateInput.value = formatted;
        dateInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // function changeCheckBox() {
    //     const checkbox = document.getElementById('tm-recurring');
    //     const checkboxStore = document.getElementById('checkbox-store');
    //     if (checkbox) {
    //             const newValue = !checkbox.checked;
    //             checkbox.checked = newValue;
                
    //             // Update both the component and the store
    //             DashClientside.setProps('tm-recurring', { value: newValue });
    //             DashClientside.setProps('checkbox-store', { data: { value: newValue } });

    //             checkbox.dispatchEvent(new Event('input', { bubbles: true }));
    //             checkboxStore.dispatchEvent(new Event('input', { bubbles: true }));
    //         }
    //     }

    function initKeyboardNavigation() {
        document.addEventListener('keydown', function (e) {
            const active = document.activeElement;
            const id = active?.id;

            // Check if we're in the dropdown or its input
            const isInDropdown = active.closest('#tm-category') !== null;

            // Only prevent default for keys we're handling
            const handledKeys = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'];
            if (handledKeys.includes(e.key)) {
                e.preventDefault();
            }

            if (e.key === 'ArrowLeft') {
                if (isInDropdown) {
                    focusPrevious('tm-category');
                } else {
                    focusPrevious(id);
                }
            } else if (e.key === 'ArrowRight') {
                if (isInDropdown) {
                    focusNext('tm-category');
                } else {
                    focusNext(id);
                }
            }

            // Handle date arrow buttons
            if (id === 'tm-date-decrement' || id === 'tm-date-increment') {
                if (e.key === 'ArrowUp') {
                    clickButton('tm-date-increment');
                } else if (e.key === 'ArrowDown') {
                    clickButton('tm-date-decrement');
                } else if (e.key === 'ArrowLeft' && id === 'tm-date-increment') {
                    const focusElement = getFocusableElement('tm-date-left-arrow');
                    if (focusElement) focusElement.focus();
                } else if (e.key === 'ArrowRight' && id === 'tm-date-decrement') {
                    const focusElement = getFocusableElement('tm-date-right-arrow');
                    if (focusElement) focusElement.focus();
                } else if (e.key === 'ArrowLeft' && id === 'tm-date-decrement') {
                    const focusElement = getFocusableElement('tm-note');
                    if (focusElement) focusElement.focus();
                } else if (e.key === 'ArrowRight' && id === 'tm-date-increment') {
                    const focusElement = getFocusableElement('tm-category');
                    if (focusElement) focusElement.focus();
                }
            }

            // Enter submits the form
            if (e.key === 'Enter') {
                const categoryDropdown = document.getElementById('tm-category');
                const isSelectingCategory = categoryDropdown && 
                                        (active === categoryDropdown || 
                                            categoryDropdown.contains(active));
                
                if (!isSelectingCategory) {
                    clickButton('add-transaction-btn');
                }
            }

            // -- Category transition handler --
            if (id === 'cm-category') {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    
                    const focusElement = getFocusableElement('cm-budget');
                    if (focusElement) focusElement.focus();
                }
            }

            if (id === 'cm-budget') {
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    
                    const focusElement = getFocusableElement('cm-category');
                    if (focusElement) focusElement.focus();
                }
            }

            // -- Income transition handler --
            if (id === 'im-source') {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    
                    const focusElement = getFocusableElement('im-amount');
                    if (focusElement) focusElement.focus();
                }
            }

            if (id === 'im-amount') {
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    
                    const focusElement = getFocusableElement('im-source');
                    if (focusElement) focusElement.focus();
                }
                
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    
                    const focusElement = getFocusableElement('im-date');
                    if (focusElement) focusElement.focus();
                }
            }

            // Date navigation handler income
            // if (id === 'im-date') {
            //     if (e.key === 'ArrowUp') {
            //         e.preventDefault();
            //         changeDateBy(1, 'im-date');
            //     } else if (e.key === 'ArrowDown') {
            //         e.preventDefault();
            //         changeDateBy(-1, 'im-date');
            //     }

            //     if (e.key === 'ArrowLeft') {
            //         e.preventDefault();
                    
            //         const focusElement = getFocusableElement('im-amount');
            //         if (focusElement) focusElement.focus();
            //     }
            // }
        });
    }

    if (document.readyState !== 'loading') {
        initKeyboardNavigation();
    } else {
        document.addEventListener('DOMContentLoaded', initKeyboardNavigation);
    }

})();