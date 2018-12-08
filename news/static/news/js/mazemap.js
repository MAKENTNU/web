$('.ui.search').search({
    apiSettings: {
        // Search for points of interest at NTNU Gløshaugen
        url: 'https://api.mazemap.com/search/equery/?q={query}&rows=5&withpois=true&campusid=1',
        // Convert mazemap search results to fit semantic ui search format
        onResponse: (mazemap_response => ({
            results: mazemap_response.result.map(item => ({
                title: (
                    item.dispPoiNames[0] +
                    (item.dispBldNames[0] ? ", " + item.dispBldNames[0] : "")
                ).replace(/<[/]?em>/g, ""),
                description: (item.dispPoiNames[1] ? item.dispPoiNames[1] : "").replace(/<[/]?em>/g, ""),
                id: item.poiId,
            }))
        })),
    },
    onSelect: function (result, response) {
        $("input[name=place_url").val(
            `https://use.mazemap.com/?campusid=1&desttype=poi&dest=${result.id}`
        );
    },
    searchDelay: 0,
    fullTextSearch: true,
});
