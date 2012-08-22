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

function filter() {
    var q = $(this).val();

    $($(this).attr("data-filter")).each(function() {
        $(this).filter(":contains('" + q + "')").show();
        $(this).filter(":not(:contains('" + q + "'))").hide();
    });
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

    $("#filter").keyup(filter).change(filter);
    filter($("#filter"));
});
