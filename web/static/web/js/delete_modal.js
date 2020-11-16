function setupDeleteModal() {
    $(".delete-modal-button").click(function (e) {
        e.preventDefault();

        // Set `action` attribute of form
        const $deleteButton = $(this);
        const url = $deleteButton.data('url');
        $("#delete-form").attr('action', url);

        // Update prompt text, if specified
        let prompt = $deleteButton.data('prompt');
        if (!prompt) {
            const objName = $deleteButton.data('obj-name');
            if (objName) {
                prompt = interpolate(
                    gettext("Are you sure you want to delete “%(objName)s”?"), {objName: objName}, true,
                );
            }
        }
        if (prompt) {
            $("#delete-modal .prompt").html(escape(prompt));
        }

        $("#delete-modal .delete.button").click(function (e) {
            $("#delete-form").submit();
        });
        $("#delete-modal").modal('show');
    });
}

function escape(str) {
    // Construct a dummy tag (`<i>`) and return the inserted (and automatically escaped) text
    return $("<i>").text(str).html();
}

setupDeleteModal();
