const $config = $("#config-from-django");
// Could have just assigned the config object directly to `$("#config-from-django").data()`,
// but this makes it more explicit which attributes are expected.
// noinspection ES6ConvertVarToLetConst
var CKEDITOR_CONFIG_FROM_DJANGO = {
    shouldAllowAllTags: $config.data("should-allow-all-tags"),
};
