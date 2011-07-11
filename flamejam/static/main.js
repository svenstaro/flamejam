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
        update: function(value) {
            if(value < 1) { value = 1; }
            if(value > this.stepcount) { value = this.stepcount; }
            this.steps.find(".step-slider-step").removeClass("on");
            for (var i = 1; i <= value; i += 1) {
                this.steps.find(".step-slider-step-" + i).addClass("on");
            }
            this.input.val(value);
        },
        initialize: function(input, stepcount) {
            var object = this;
            this.input = input;
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
            this.input.mousemove(function() { object.update($(this).val()); return false; });
            this.update(this.input.val());
        },
        stepclick: function($$) {
            this.update(this.steps.find(".step-slider-step").index($$) + 1);
        }
    };
}

$(document).ready(function() {
    $('ul.screenshots li a').lightBox({
        imageLoading: "{{ url_for('static', filename = 'gfx/lightbox-ico-loading.gif') }}",
        imageBtnClose: "{{ url_for('static', filename = 'gfx/lightbox-btn-close.gif') }}",
        imageBtnPrev: "{{ url_for('static', filename = 'gfx/lightbox-btn-prev.gif') }}",
        imageBtnNext: "{{ url_for('static', filename = 'gfx/lightbox-btn-next.gif') }}",
        imageBlank: "{{ url_for('static', filename = 'gfx/lightbox-blank.gif') }}",
        txtImage: "Screenshot",
        fixedNavigation: true
    });

    $("input.slider").step_slider();
});
