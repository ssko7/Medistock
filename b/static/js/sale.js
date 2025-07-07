function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'block';
    }
}

// Close modal when clicking the close button or outside the modal content
document.addEventListener('DOMContentLoaded', function () {
    const modals = document.querySelectorAll('.modal');

    modals.forEach(modal => {
        const closeBtn = modal.querySelector('.close-btn');
        const cancelBtn = modal.querySelector('.btn-secondary', modal);

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                modal.style.display = 'none';
            });
        }

        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    const addProductBtn = document.querySelector('.add-product');
    const productsList = document.querySelector('.products-list');
    const totalSection = document.querySelector('.total-section');

    if (addProductBtn && productsList) {
        const productEntryTemplate = document.querySelector('.product-entry'); // select once
    
        addProductBtn.addEventListener('click', function () {
            const newProductEntry = productEntryTemplate.cloneNode(true);
            newProductEntry.querySelectorAll('input, select').forEach(input => {
                input.value = ''; // reset values
            });
            productsList.appendChild(newProductEntry);
            attachInputListeners(newProductEntry);
        });
    }
    

    function attachInputListeners(entry) {
        const quantityInput = entry.querySelector('input[placeholder="Quantity"]');
        const priceInput = entry.querySelector('input[placeholder="Unit Price"]');
        const totalInput = entry.querySelector('input[placeholder="Total"]');
        const removeBtn = entry.querySelector('.remove-product');

        function updateTotal() {
            const quantity = parseFloat(quantityInput.value) || 0;
            const unitPrice = parseFloat(priceInput.value) || 0;
            totalInput.value = (quantity * unitPrice).toFixed(2);
            updateGrandTotal();
        }

        quantityInput.addEventListener('input', updateTotal);
        priceInput.addEventListener('input', updateTotal);

        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                entry.remove();
                updateGrandTotal();
            });
        }
    }

    function updateGrandTotal() {
        const totals = document.querySelectorAll('.product-entry input[placeholder="Total"]');
        let subtotal = 0;
        totals.forEach(input => {
            subtotal += parseFloat(input.value) || 0;
        });

        // Get GST % dynamically from input field
        const gstPercentInput = document.getElementById('gstPercent');
        const gstPercent = parseFloat(gstPercentInput?.value) || 0;

        const gstAmount = subtotal * gstPercent / 100;

        // Get discount dynamically from input field
        const discountInput = document.getElementById('discount');
        const discountAmount = parseFloat(discountInput?.value) || 0;

        const grandTotal = subtotal + gstAmount - discountAmount;

        const totalRows = totalSection.querySelectorAll('.total-row span:last-child');
        if (totalRows.length >= 4) {
            totalRows[0].textContent = `₹${subtotal.toFixed(2)}`;         // Subtotal
            totalRows[1].textContent = `₹${gstAmount.toFixed(2)}`;         // GST
            totalRows[2].textContent = `₹${discountAmount.toFixed(2)}`;    // Discount
            totalRows[3].textContent = `₹${grandTotal.toFixed(2)}`;        // Grand Total
        }
        const subtotalHidden = document.getElementById('subtotal-hidden');
        const gstHidden = document.getElementById('gst-hidden');
        const discountHidden = document.getElementById('discount-hidden');
        const grandtotalHidden = document.getElementById('grandtotal-hidden');
    
        if (subtotalHidden) subtotalHidden.value = subtotal.toFixed(2);
        if (gstHidden) gstHidden.value = gstAmount.toFixed(2);
        if (discountHidden) discountHidden.value = discountAmount.toFixed(2);
        if (grandtotalHidden) grandtotalHidden.value = grandTotal.toFixed(2);
    }

    // When user changes GST % or Discount, recalculate totals
    const gstInput = document.getElementById('gstPercent');
    const discountInput = document.getElementById('discount');

    if (gstInput) {
        gstInput.addEventListener('input', updateGrandTotal);
    }

    if (discountInput) {
        discountInput.addEventListener('input', updateGrandTotal);
    }

    // Attach listeners for the default first product-entry
    const defaultProductEntry = document.querySelector('.product-entry');
    if (defaultProductEntry) {
        attachInputListeners(defaultProductEntry);
    }
});
