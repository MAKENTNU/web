$('.ui.search')
    .search({
        apiSettings: {
            onResponse: function (mazemap_response) {
                let response = {results: []};
                $.each(mazemap_response.result, function (index, item) {
                    let room_details = {
                        title: item.poiNames[1] + " (" + item.poiNames[0] + ")",
                        description: item.dispBldNames + " " + item.zName,
                    };
                    response.results.push(room_details);
                });
                return response;
            },
            url: 'https://api.mazemap.com/search/equery/?q={query}&rows=10&start=0&withpois=true&withbuilding=false&withtype=false&withcampus=false&campusid=1'
        }
    })
;

