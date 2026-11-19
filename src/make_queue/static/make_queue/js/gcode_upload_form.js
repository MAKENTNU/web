// Check the file size before uploading, as Nginx on the server would otherwise reject a
// too large file with a generic error page - and only after the whole file has been sent
const $fileInput = $("input[type=file][data-max-size]");

$fileInput.on("change", function () {
    const file = this.files[0];
    const maxSize = Number($(this).data("max-size"));
    if (file && file.size > maxSize) {
        const message = gettext("The file is too large (%(size)s). The maximum size is %(max_size)s.");
        this.setCustomValidity(interpolate(message, {
            size: formatFileSize(file.size),
            max_size: formatFileSize(maxSize),
        }, true));
    } else {
        this.setCustomValidity("");
    }
    this.reportValidity();
});

// Uploading can take a while, so show that it's in progress
$fileInput.closest("form").on("submit", function () {
    $(this).find("input[type=submit]")
        .val(gettext("Uploading…"))
        .addClass("disabled");
});

/** Formats the same way as Django's `filesizeformat` filter does on this site. */
function formatFileSize(bytes) {
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
