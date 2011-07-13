// countdown.js

$.fn.countdown = function() {
    var field = $(this);



};

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

        var end_utc = new Date(t);
        var end_utc_msec = end_utc.getTime();

        var local = new Date();
        var local_msec = local.getTime();
        var local_offset = local.getTimezoneOffset() * 60000;
        var local_utc_msec = local_msec + local_offset;

        var diff_msec = end_utc_msec - local_msec;
        // we lose an hour somewhere, probably JS counts since "1970-1-1 01:00" or so
        // test and monitor this!
        diff_msec += 3600000;

        if(diff_msec < 0) {
            return;
        }
        var diff = new Date(diff_msec);

        var times = new Array(
            diff.getDate() - 1,
            diff.getHours(),
            diff.getMinutes(),
            diff.getSeconds()
            );

        times[0] = leadingZero(times[0], 2);
        times[1] = leadingZero(times[1], 2);
        times[2] = leadingZero(times[2], 2);
        times[3] = leadingZero(times[3], 2);

        for (var i = 0; i <= 9; i += 1) {
            $(this).find(".digit").removeClass("n" + i);
        }

        $(this).find(".d0").addClass("n" + times[0][0]);
        $(this).find(".d1").addClass("n" + times[0][1]);
        $(this).find(".h0").addClass("n" + times[1][0]);
        $(this).find(".h1").addClass("n" + times[1][1]);
        $(this).find(".m0").addClass("n" + times[2][0]);
        $(this).find(".m1").addClass("n" + times[2][1]);
        $(this).find(".s0").addClass("n" + times[3][0]);
        $(this).find(".s1").addClass("n" + times[3][1]);

        if(times[1] < 1) {
            // less than 1 hour
            $(this).find(".time").addClass("red");
        } else {
            $(this).find(".time").removeClass("red");
        }

        if(! $(this).hasClass("countdown")) {
            $(this).find(".time").text(times.join(":"));
        }
        /*$(this).attr("time", times.join(":"));
        */
    });

    setTimeout(countdown, 1000);
}

$(document).ready(function() {
    countdown();
});
