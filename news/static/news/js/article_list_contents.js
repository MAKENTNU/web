const MAX_HEIGHT_PX = 500;

// Manually set the height of the article images, as it was not possible to find CSS styling that yielded the same result
$(".articles .article-img-container img").load(function () {
    const $articleImage = $(this);
    if (!$articleImage.hasClass("contain"))
        $articleImage.height(Math.min(this.naturalHeight, MAX_HEIGHT_PX));
});
