// http://stackoverflow.com/a/2196683/402551
// Thanks, Nick Craver!
jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
    return function( elem ) {
        return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

function parseMarkdown(input, callback) {
    $.ajax({
        type: "POST",
        url: "/ajax/markdown",
        cache: false,
        data: "input=" + input,
        success: callback
    });
}

function updatePreview() {
    parseMarkdown('# ' + $("#announcement-subject").val() + "\n\n" + $("#announcement-message").val(),
        function(data) {
            $("#announcement-preview").html(data);
        });
}

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
        $(this).filter(":Contains('" + q + "')").show();
        $(this).filter(":not(:Contains('" + q + "'))").hide();
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

    $(".announcement-input").change(updatePreview);
});
