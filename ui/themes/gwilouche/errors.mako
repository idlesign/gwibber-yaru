<%namespace name="base" file="base.mako">
</%namespace>

<html>
  <head>
    <script src="jquery.js"></script>
    <style>
      <%include file="theme.css" /> 
    </style>
    <script>
      $(document).ready(function() {
        $(".toggledupe").show(0).unbind().toggle(
          function() {$(this).parent().parent().find(".dupes").show(100)},
          function() {$(this).parent().parent().find(".dupes").hide(100)});
      });
    </script>
  </head>
  <body>
    <div class="welcome">
      <h2>Errors</h2>
    </div>
    % if message_store:
      ${base.errors(message_store)}
    % endif
  </body>
</html>
