document.addEventListener('DOMContentLoaded', function () {
    // Modal controls
    window.showModal = modalId => document.getElementById(modalId).classList.add('active');
    window.hideModal = modalId => document.getElementById(modalId).classList.remove('active');

    // Close modals on close button or outside click
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', () => btn.closest('.modal').classList.remove('active'));
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', e => {
            if (e.target === modal) modal.classList.remove('active');
        });
    });

    // Initialize TomSelect dropdowns
    function initSelectDropdown(el) {
        if (el.tomselect) return;

        const rawData = el.dataset.medicines || '';
        const medicines = rawData.split(',').map(item => {
            const [id, name] = item.split('|');
            return { id, name };
        });

        new TomSelect(el, {
            valueField: 'id',
            labelField: 'name',
            searchField: 'name',
            options: medicines,
            create: false,
            sortField: { field: "text", direction: "asc" },
            placeholder: "Select or search medicine",
            closeAfterSelect: true,
            dropdownParent: document.body,
            score: search => item => {
                const name = item.name.toLowerCase();
                search = search.toLowerCase();
                return name.startsWith(search) ? 100 :
                    name.includes(search) ? 50 : 0;
            },
            render: {
                option: data => `<div>${data.name}</div>`,
                item: data => `<div>${data.name}</div>`
            },
            onFocus() {
                this.unlock();
            },
            onKeydown(e) {
                if (e.keyCode === 8 && this.items.length > 0) this.clear();
            },
            onLoad() {
                this.refreshOptions();
            },
            onDropdownOpen() {
                const rect = this.control.getBoundingClientRect();
                Object.assign(this.dropdown.style, {
                    top: `${rect.bottom + window.scrollY + 5}px`,
                    left: `${rect.left + window.scrollX}px`,
                    position: 'absolute',
                    zIndex: 9999
                });
            },
            onChange(value) {
                const parent = this.wrapper.closest('.product-entry');
                const otherInput = parent.querySelector('.other-medicine');
                if (value === 'other') {
                    otherInput.style.display = 'block';
                    this.control.removeAttribute('tabindex');
                    this.blur();
                } else {
                    otherInput.style.display = 'none';
                }
            }
        });
    }

    const form = document.getElementById('purchaseForm');
    const productsList = form.querySelector('.products-list');
    const gstInput = form.querySelector('#gstPercent');
    const discountInput = form.querySelector('#discount');
    const subtotalDisplay = document.getElementById('subtotal');
    const gstAmountDisplay = document.getElementById('gst-amount');
    const discountAmountDisplay = document.getElementById('discount-amount');
    const grandTotalDisplay = document.getElementById('grand-total');
    const gstLabel = document.getElementById('gstLabel');

    function updateTotals() {
        let subtotal = 0;

        productsList.querySelectorAll('.product-entry').forEach(entry => {
            const quantity = parseFloat(entry.querySelector('.quantity').value) || 0;
            const rate = parseFloat(entry.querySelector('.rate').value) || 0;
            const amount = quantity * rate;

            const amountInput = entry.querySelector('.amount');
            if (amountInput) {
                amountInput.value = amount.toFixed(2);
            }

            subtotal += amount;
        });

        const gstPercent = parseFloat(gstInput.value) || 0;
        const discount = parseFloat(discountInput.value) || 0;
        const gstAmount = subtotal * gstPercent / 100;
        const grandTotal = subtotal - gstAmount - discount;

        subtotalDisplay.textContent = `₹${subtotal.toFixed(2)}`;
        gstAmountDisplay.textContent = `₹${gstAmount.toFixed(2)}`;
        discountAmountDisplay.textContent = `₹${discount.toFixed(2)}`;
        grandTotalDisplay.textContent = `₹${grandTotal.toFixed(2)}`;
        gstLabel.textContent = `GST (${gstPercent}%)`;
        document.getElementById('grandTotalInput').value = grandTotal.toFixed(2);

    }

    // Live calculation when inputs change
    form.addEventListener('input', function (e) {
        if (e.target.matches('.quantity, .rate, #gstPercent, #discount')) {
            updateTotals();
        }
    });

    // Add product entry
    const addBtn = form.querySelector('.add-product');
    addBtn.replaceWith(addBtn.cloneNode(true)); // removes all old listeners
    
    form.querySelector('.add-product').addEventListener('click', function () {
        const entries = productsList.querySelectorAll('.product-entry');
        const newIndex = entries.length;
        const template = entries[0].cloneNode(true);
    
        // Replace index in input names
        template.innerHTML = template.innerHTML.replace(/products\[\d+\]/g, `products[${newIndex}]`);
    
        // Clear input values
        template.querySelectorAll('input').forEach(input => input.value = '');
        const otherInput = template.querySelector('.other-medicine');
        if (otherInput) {
            otherInput.style.display = 'none';
        }
    
        // Reset dropdown if needed
        const newSelect = template.querySelector('.medicine-select');
        if (newSelect) {
            if (newSelect.tomselect) {
                newSelect.tomselect.destroy();
            }
            newSelect.innerHTML = ''; // Clear current options
            newSelect.dataset.medicines = entries[0].querySelector('.medicine-select').dataset.medicines;
            initSelectDropdown(newSelect);
        }
    
        productsList.appendChild(template);
        updateIndexes();
        updateTotals();
    });
    
    
    // Remove product entry
    productsList.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-product')) {
            const entries = productsList.querySelectorAll('.product-entry');
            if (entries.length > 1) {
                e.target.closest('.product-entry').remove();
                updateIndexes();
                updateTotals();
            }
        }
    });

    // Update index names after deletion
    function updateIndexes() {
        productsList.querySelectorAll('.product-entry').forEach((entry, index) => {
            entry.querySelectorAll('input, select').forEach(el => {
                el.name = el.name.replace(/products\[\d+\]/, `products[${index}]`);
            });
        });
    }

    // Initial setup
    document.querySelectorAll('.medicine-select').forEach(initSelectDropdown);
    updateTotals();
});
