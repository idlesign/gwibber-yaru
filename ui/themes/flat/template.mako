<%namespace name="base" file="base.mako">
  <%def name="msgstyle(data)">
    background: rgba(${data["color"].rgb}, 0.15);
  </%def>
</%namespace>

<html>
  <head>
    <script src="jquery.js"></script>
    <script>
      $(document).ready(function() {
        $(".message").hover(
          function() {$(this).find(".hidden").css("visibility", "visible")},
          function() {$(this).find(".hidden").css("visibility", "hidden")});

        $(".toggledupe").show(0).unbind().toggle(
          function() {$(this).closest(".basemsg").find(".dupes").show(100)},
          function() {$(this).closest(".basemsg").find(".dupes").hide(100)});
      });
    </script>
    <style>
      <%include file="theme.css" /> 
    </style>
  </head>
  <body>
    ${base.messages(message_store)}
  </body>
</html>
