var geocoder, map, options, clusterer, spiderer, info;
var SIZE = 16;

var LIGHTNESS = -70;
var STYLE = [
    {elementType:"labels",stylers: [{visibility:"off"}]},
    {featureType:"water",stylers:[{visibility:"simplified"},{saturation:-100},{lightness:LIGHTNESS}]},
    {featureType:"poi",stylers: [{visibility:"off"}]},
    {featureType:"landscape.natural",stylers:[{visibility:"simplified"},{saturation:-100},{lightness:LIGHTNESS*0.9}]},
    {featureType:"administrative",stylers:[{visibility:"on"},{saturation:-100},{lightness:LIGHTNESS*0.7}]},
    {featureType:"road",stylers:[{visibility:"off"}]},
    {featureType:"transit",stylers:[{visibility:"off"}]},
    {featureType:"landscape.man_made",stylers:[{saturation:-100},{lightness:LIGHTNESS*0.9}]},
    {featureType:"administrative.locality",stylers:[{visibility:"off"}]}
];

function applyStyle() {
    var styledMap = new google.maps.StyledMapType(STYLE, {name: "Styled Map"});
    map.mapTypes.set('map_style', styledMap);
    map.setMapTypeId('map_style');
}

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
        // icon: image,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 5,
            fillColor: '#FA0',
            fillOpacity: 0.5,
            strokeColor: '#FA0',
            strokeWeight: 1,
        },
    });
    marker.username = info[0];

    spiderer.addMarker(marker);
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
    applyStyle();

    spiderer = new OverlappingMarkerSpiderfier(map);
    spiderer.legColors.usual["map_style"] = "#F90";
    spiderer.legColors.highlighted["map_style"] = "#FFF";

    info = new google.maps.InfoWindow();
    spiderer.addListener("click", function(marker, event) {

        $.ajax({
            type: "GET",
            url: "/ajax/map-user/" + marker.username + "/",
            dataType: "text",
            cache: false,
            success: function(data) {
                info.setContent(data);
                info.open(map, marker);
            },
            error: function(data, m) {
                info.setContent("Error: " + m);
                info.open(map, marker);
            }
        });

    });

    map.addListener("click", function() {
        info.close();
    });

    spiderer.addListener("spiderfy", function(markers) {
        info.close();
    });

    for(var i = 0; i < locations.length; ++i) {
        addLocation(locations[i]);
    }
});
