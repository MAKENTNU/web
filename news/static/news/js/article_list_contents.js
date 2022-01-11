/**
 * This script must be linked using the `defer` attribute!
 */

const MAX_HEIGHT_PX = 500;

// Manually set the height of the article images, as it was not possible to find CSS styling that yielded the same result
$(".articles .article-img-container img").one("load", function () {
    const $articleImage = $(this);
    if ($articleImage.hasClass("contain"))
        return;
    if (!this.naturalHeight) {
        console.error({
            message: "Image missing `naturalHeight` - probably because it was not completely loaded.",
            image: this, naturalHeight: this.naturalHeight,
        });
    }

    $articleImage.height(Math.min(this.naturalHeight, MAX_HEIGHT_PX));
}).each(function () {
    // Code based on https://stackoverflow.com/a/3877079
    if (this.complete)
        $(this).trigger("load");
});
