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

        if (t == "00:00:00:00") {
            return;
        }

        var times = t.split(/[^0-9]/);

        times[3] -= 1;
        if (times[3] < 0) {
            times[3] += 60;
            times[2] -= 1;
        }
        if (times[2] < 0) {
            times[2] += 60;
            times[1] -= 1;
        }
        if (times[1] < 0) {
            times[0] += 24;
            times[0] -= 1;
        }

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
        $(this).attr("time", times.join(":"));
    });

    setTimeout(countdown, 1000);
}

$(document).ready(function() {
    setTimeout(countdown, 1000);
});
