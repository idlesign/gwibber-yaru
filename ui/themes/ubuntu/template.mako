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


  <%def name="getStateClass(data)" filter="trim">
    % if data.get("sender", {}).get("is_me", 0):
      outgoingItem 
    % else:
      % if data.get("to_me", 0) or data.get("private", 0):
        incomingReply
      % else:
        incomingItem
      % endif
    % endif      
  </%def>

  <%def name="message(data)">
    <div class="chatItem ${getStateClass(data)}">

		<table width="100%">
			<tr>
				<td valign="top">
          ${base.sidebar(data)}
					<div class="myBubble">
						<div class="indicator"></div>
						<table class="tableBubble" cellspacing="0" cellpadding="0">
							<tr>
								<td class="tl"></td>
								<td class="tr"></td>
							</tr>
							<tr>
								<td class="message">
                  ${base.content(data)}
                  ${base.fold(data)}
                  ${base.dupes(data)}
                </td>
                <td class="buttons messageRight">
                  ${base.toggledupe(data)}
                  <div class="hidden">
                  ${base.buttons(data)}
                  </div>
								</td>
							</tr>
							<tr>
								<td class="bl"></td>
								<td class="br"></td>
							</tr>
						</table>
					</div>
				</td>
			</tr>
		</table>
	</div>

  </%def>
</%namespace>

<html>
  <head>
    <script src="jquery.js"></script>
    <script>
      $(document).ready(function() {
        $(".tableBubble").hover(
          function() {$(this).find(".hidden").css("visibility", "visible")},
          function() {$(this).find(".hidden").css("visibility", "hidden")});

        $(".toggledupe").show(0).unbind().toggle(
          function() {$(this).parent().parent().find(".dupes").show(100)},
          function() {$(this).parent().parent().find(".dupes").hide(100)});
      });
    </script>
    <style>
      <%include file="css.mako" />
      <%include file="defaultcss.mako" />
      <%include file="main.css" />
    </style>
  </head>
  <body>
    ${base.messages(message_store)}
  </body>
</html>
