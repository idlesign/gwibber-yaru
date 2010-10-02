<%namespace name="base" file="base.mako">
  <%def name="msgstyle(data)">
    background: -webkit-gradient(linear, left top, left 250%, 
      from(${theme["bg"].hex}),
      to(${theme["bg"].darker(.70).hex}));

    -webkit-border-radius: 0;
    border: 2px solid ${data["color"].hex};
    border-left: 7px solid ${data["color"].hex};
    margin: 2px;
    padding: 2px;
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
      <%include file="css.mako" />
      <%include file="defaultcss.mako" />

      .imgbox {
        width: 35px;
        height: 35px;
      }
    </style>
  </head>
  <body>
    ${base.messages(message_store)}
  </body>
</html>
