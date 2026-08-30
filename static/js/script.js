/**
 * SIH26032: Smart Farmer Procurement System - Main Script
 */

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alert banners after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // Dynamic MSP Calculation in Booking Form
    const cropSelect = document.getElementById('crop_select');
    const quantityInput = document.getElementById('crop_quantity');
    const mspCalcDisplay = document.getElementById('msp_calculated_display');

    function updateExpectedAmount() {
        if (!cropSelect || !quantityInput || !mspCalcDisplay) return;
        const selectedOpt = cropSelect.options[cropSelect.selectedIndex];
        if (selectedOpt && selectedOpt.dataset.msp) {
            const mspRate = parseFloat(selectedOpt.dataset.msp) || 0;
            const qty = parseFloat(quantityInput.value) || 0;
            const total = mspRate * qty;
            mspCalcDisplay.innerHTML = `<strong>Estimated Value (MSP):</strong> ₹${total.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})} <span class="text-muted">(@ ₹${mspRate.toLocaleString('en-IN')}/Qtl)</span>`;
        } else {
            mspCalcDisplay.innerHTML = '';
        }
    }

    if (cropSelect && quantityInput) {
        cropSelect.addEventListener('change', updateExpectedAmount);
        quantityInput.addEventListener('input', updateExpectedAmount);
        updateExpectedAmount();
    }
});
