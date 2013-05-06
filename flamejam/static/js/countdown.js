function leadingZero(num, count) {
    var r = num + '';
    while(r.length < count) {
        r = "0" + r;
    }
    return r;
}

function countdown() {
    $(".countdown, .home-countdown, .mini-countdown").each(function() {
        var t = $(this).attr("time");
        if(t == null) {
            return;
        }

        var end_utc = new Date(t + " UTC");
        if (isNaN(end_utc.getTime())) {
            end_utc = new Date(t.split(".")[0].replace(/-/g, "/") + " UTC");
        }

        var now_utc = new Date();
        var diff_msec = new Date(end_utc - now_utc);

        if(diff_msec < 0) {
            return;
        }

        var ds = Math.floor(diff_msec / 1000);
        var ms = diff_msec - ds * 1000;

        var days = Math.floor(ds / 60 / 60 / 24);
        ds = ds - days * 60 * 60 *  24;

        var hours = Math.floor(ds / 60 / 60);
        ds = ds - hours * 60 * 60;

        var minutes = Math.floor(ds / 60);
        ds = ds - minutes * 60;

        var seconds = ds;

        $(this).find(".time-d").text(days);
        $(this).find(".time-h").text(leadingZero(hours, 2));
        $(this).find(".time-m").text(leadingZero(minutes, 2));
        $(this).find(".time-s").text(leadingZero(seconds, 2));
    });

    setTimeout(countdown, 1000);
}

$(document).ready(function() {
    countdown();
});

