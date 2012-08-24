function updateCheckedCount() {
    var l = $("#checkbox-toggle-table").find(":checkbox:checked").length;
    $("#table-count").text(l);
}

function setCheckboxRowStatus(r) {
    var c = r.find("input:checkbox").attr("checked");
    r.removeClass("on").removeClass("off");
    if(c) r.addClass("on");
    else r.addClass("off");

    updateCheckedCount();
}

function filter(v) {
    var q = v.val();

    $(v.attr("data-filter")).each(function() {
        $(this).filter(":contains('" + q + "')").show();
        $(this).filter(":not(:contains('" + q + "'))").hide();
    });
}

function updateDays(d) {
    var h = d.parent(".field").find("input").val();
    d.text("= " + (Math.round(h / 24 * 20) / 20) + " days");
}

$(document).ready(function() {
    $(".checkbox-toggle").click(function(event) {
        if (event.target.type !== 'checkbox') {
            $(':checkbox', this).trigger('click');
        }
        setCheckboxRowStatus($(this));
    }).each(function() {
        setCheckboxRowStatus($(this));
    });

    $(".checkbox-toggle input:checkbox").change(function() {
        setCheckboxRowStatus($(this).parent("tr.checkbox-toggle"));
        return false;
    });

    // --------------------------------------------------------------

    $("#filter").keyup(function() { filter($(this)); }).change(function() { filter($(this)); });
    filter($("#filter"));

    // --------------------------------------------------------------
    $(".field .days").each(function() {
        var d = $(this);
        d.parent(".field").find("input").change(function() {
            updateDays(d);
        }).keyup(function() {
            updateDays(d);
        });
        updateDays(d);
    });
});
