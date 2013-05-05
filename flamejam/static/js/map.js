var geocoder, map, options, clusterer;
var SIZE = 16;

var people = [{
        url: '/static/gfx/map/cluster-2.png',
        height: 32,
        width: 32,
        anchor: [6, 11],
        textColor: '#000',
        textSize: 16
      }, {
        url: '/static/gfx/map/cluster-3.png',
        height: 32,
        width: 32,
        anchor: [6, 6],
        textColor: '#000',
        textSize: 16
      }, {
        url: '/static/gfx/map/cluster-4.png',
        height: 32,
        width: 32,
        anchor: [6, 11],
        textColor: '#000',
        textSize: 12
      }];

function addLocation(info) {
    var image = new google.maps.MarkerImage(info[2],
        new google.maps.Size(SIZE, SIZE),
        new google.maps.Point(0,0),
        new google.maps.Point(SIZE / 2, SIZE / 2));

    var s = info[1].split(",");
    var pos = new google.maps.LatLng(s[0], s[1]);

    marker = new google.maps.Marker({
        position: pos,
        map: map,
        title: info[0],
        icon: image
    });

    clusterer.addMarker(marker);
}

$(document).ready(function() {
    // size and scrolling
    var w = $(window), m = $("#map_canvas");
    m.height(w.height() * 0.9);
    $(window).scrollTop (m.offset().top  + m.height() / 2 - w.height() / 2);
    $(window).scrollLeft(m.offset().left + m.width()  / 2 - w.width()  / 2);

    geocoder = new google.maps.Geocoder();

    options = {
        center: new google.maps.LatLng(30, 0),
        zoom: 2,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    map = new google.maps.Map(document.getElementById("map_canvas"), options);

    clusterer = new MarkerClusterer(map, [], {
        styles: people
        });

    for(var i = 0; i < locations.length; ++i) {
        addLocation(locations[i]);
    }
});
