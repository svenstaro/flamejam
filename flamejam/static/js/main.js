_step_sliders = new Array();

$.fn.step_slider = function() {
    $(this).each(function() {
        s = step_slider();
        s.initialize($(this), 10);
    });
};

function step_slider() {
    return {
        input: null,
        steps: null,
        stepcount: 1,
        enabled: true,
        value: 5,
        update: function(value) {
            if(value < 1) { value = 1; }
            if(value > this.stepcount) { value = this.stepcount; }
            this.steps.find(".step-slider-step").removeClass("on");
            for (var i = 1; i <= value; i += 1) {
                this.steps.find(".step-slider-step-" + i).addClass("on");
            }
            this.input.val(value);
        },
        setEnabled: function(enabled) {
            this.input.attr("disabled", !enabled);
            this.checkbox.attr("checked", !enabled);
            if(enabled) {
                this.steps.removeClass("disabled");
            } else {
                this.steps.addClass("disabled");
            }
        },
        initialize: function(input, stepcount) {
            var object = this;
            this.input = input;
            this.value = input.val();
            this.checkbox = input.parent().parent().find(":checkbox");
            this.stepcount = stepcount;
            this.steps = $('<div class="step-slider"></div>');
            for (var i = 1; i <= this.stepcount; i += 1) {
                step = $('<div class="step-slider-step step-slider-step-' + i + '">' + i + '</div>');
                step.click(function() { object.stepclick(this); return false; });
                step.mousemove(function(e) { if(e.button) { object.stepclick(this); } return false; });
                this.steps.append(step);
            }
            this.input.after(this.steps);
            this.input.change(function() { object.update($(this).val()); return false; });
            this.input.keyup(function() { object.update($(this).val()); return false; });
            this.input.click(function() { object.update($(this).val()); return false; });
            this.checkbox.change(function() { object.setEnabled(!$(this).attr("checked")); });
            this.update(this.input.val());
            this.setEnabled(!this.checkbox.attr("checked"));
        },
        stepclick: function($$) {
            this.update(this.steps.find(".step-slider-step").index($$) + 1);
        }
    };
}

function clearFlashes() {
    $("#flashes li").slideUp(200);
}

function sortValue(x) {
    if(x.attr("data-value")) {
        return x.attr("data-value").toLowerCase();
    }
    return x.text().toLowerCase();
}

$(document).ready(function() {
    $("input.slider").step_slider();
    $(".refresh").click(function() { location.reload(true); });

    setTimeout("clearFlashes()", 5000);

    $(".sorters th, .sorters td").click(function() {
        var pAsc = $(this).hasClass("asc");
        var pDesc = $(this).hasClass("desc");

        var asc = (!pAsc && !pDesc) || (pDesc && !pAsc);
        var desc = !asc;

        var row = $(this).parent();
        var table = row.closest("table");

        table.find("th, td").removeClass("asc").removeClass("desc");
        $(this).addClass(desc ? "desc" : "asc");

        var index = $(this).index();

        var list = table.find("tr:not(.sorters)").get();

        list.sort(function(a, b) {
            return sortValue($(a).find("td").eq(index)).localeCompare(sortValue($(b).find("td").eq(index)));
        });

        if(desc) list.reverse();

        for (var i = 0; i < list.length; i++) {
            list[i].parentNode.appendChild(list[i]);
        }
    });
});
