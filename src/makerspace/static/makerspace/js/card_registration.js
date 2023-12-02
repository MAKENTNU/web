$(document).ready(function() {
    if (window.location.search.includes('success=true')) {
        $('#success-modal').fadeIn();
    }
    $('.card-registration-modal-button').on('click', function() {
        $('#success-modal').fadeOut();
    });
});
