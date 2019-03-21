jQuery.fn.extend({
    mazemapSearch: function () {
        let data = this.data();
        this.parent().search({
            searchDelay: 0,
            fullTextSearch: true,
            apiSettings: {
                // Search for points of interest at given campus
                url: `https://api.mazemap.com/search/equery/?q={query}` +
                    `&withpois=true&withbuilding=false&withtype=false&withcampus=false` +
                    `&rows=${data.maxresults}` +
                    `&campusid=${data.campusid}`,

                // Convert MazeMap search results to fit Semantic UI search format
                onResponse: (mazemapResponse => ({
                    results: mazemapResponse.result.map(item => ({
                        title: (
                            item.dispPoiNames[0] +
                            (item.dispBldNames[0] ? ", " + item.dispBldNames[0] : "")
                        ).replace(/<[^>]*>/g, ""),
                        description: (item.dispPoiNames[1] ? item.dispPoiNames[1] : "").replace(/<[^>]*>/g, ""),
                        id: item.poiId,
                    })),
                })),
            },
            templates: {
                // Template for error messages. Default provided by Semantic UI but with translations
                message: (type, message) => (
                    `<div class="message empty">
                    <div class="header">
                        ${gettext("No Results")}
                    </div>
                    <div class="description">
                        ${gettext("Your search returned no results")}
                    </div>
                </div>`
                ),
            },
            // Autofill of MazeMap-URL if url_field is given
            onSelect: function (result, response) {
                if (data.urlfield) {
                    $(`input[name=${data.urlfield}]`).val(
                        `https://use.mazemap.com/?campusid=${data.campusid}&desttype=poi&dest=${result.id}`
                    );
                }
            },
        });
    },
});
