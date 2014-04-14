(function($) { $(function() {
  // Find all stacked inlines (they have an h3, with a span.inline_label).
  // Add a link to toggle collapsed state.
  $('.inline-group h3 .inline_label').append(' (<a class="collapse-toggle" href="#">Show</a>)');
  // Collapse all fieldsets that are in a stacked inline (not .tabular)
  $('.inline-group :not(.tabular) fieldset').addClass('collapsed');
  // Click handler: toggle the related fieldset, and the content of our link.
    $( document ).on('click', '.inline-group h3 .inline_label .collapse-toggle', function(evt) {
    $(this).closest('.inline-related').find('fieldset').toggleClass('collapsed');
    text = $(this).html();
    if (text=='Show') {
      $(this).html('Hide');
    } else {
      $(this).html('Show');
    };
    evt.preventDefault();
    evt.stopPropagation();
  });
  // Un-collapse empty forms, otherwise it's 2 clicks to create a new one.
  $('.empty-form .collapse-toggle').click();
  // Un-collapse any objects with errors.
  $('.inline-group .errors').closest('.inline-related').find('.collapse-toggle').click();
})})(jQuery || django.jQuery)
