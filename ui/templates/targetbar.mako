<%
def breakdance(name, size=22):
  return resources.get_ui_asset("icons/breakdance/%sx%s/%s.png" % (size, size, name))

def act(name):
  return {
    "reply": _("Replying to {0} as {1}"),
    "repost": _("Reposting from {0} as {1}"),
    "title": "{0} ({1})",
    "disabledtitle": _("{0} ({1}) - Disabled")
  }[name]
%>

<%def name="shine()" filter="trim">
  -webkit-gradient(linear, left top, left bottom, from(rgba(0, 0, 0, 0.45)), to(rgba(255, 255, 255, 0.42)), color-stop(0.4, rgba(0, 0, 0, 0.15)), color-stop(0.6, rgba(0, 0, 0, 0.0)), color-stop(0.9, rgba(255, 255, 255, 0.06)))
</%def>

<%def name="convex()" filter="trim">
  -webkit-gradient(linear, left top, left bottom, from(rgba(255, 255, 255, 0.3)), to(rgba(255, 255, 255, 0.45)))
</%def>

<%def name="user(target)" buffered="True">
  <div class="account" style="${accountcss(target["account_data"])}">
    <img style="padding:0px; margin:0px;" src="${breakdance(target["protocol"], 16)}" />
    ${target["account_data"]["username"]}
    <img class="closebutton" src="${resources.icon('gtk-close')}" />
  </div>
</%def>

<%def name="accountcss(account)" filter="trim">
  % if account["send_enabled"]:
    background: ${account["color"]} ${convex()};
    border: 1px solid ${account["color"]};
  % else:
    background: ${account["color"]};
    border: 1px solid rgba(255, 255, 255, 0);
    opacity: 0.5;
  % endif
</%def>


<html>
  <head>
    <script src="jquery.js"></script>
    <script>
      $(document).ready(function() {
          $(".account").click(function() {
              document.location = "gwibber:/account?id=" + $(this).attr("id") + "&send_enabled=" + Boolean($(this).attr("enabled") == "false");
          });

          $(".closebutton").click(function() {
            document.location = "gwibber:/cancel";
            return false;
          });
      });
    </script>

    <style>
      body {
        background: ${theme["bg"].hex};
        margin: 0px;
        padding: 0px;
        -webkit-user-select: none;
      }

      img { 
        -webkit-user-drag: none;
      }

      .account {
        padding: 2px;
        display: inline-block;
        -webkit-border-radius: 5px;
      }

      .reply { display: inline-block; }
      .reply img { vertical-align: middle; }
      .reply .account { padding: 2px; }
      .reply .account img { vertical-align: top; }
      .buttons .label { display: inline-block; vertical-align: super; }
      .label { color: ${theme['fg'].hex}; }
    </style>
  </head>
  <body>

    <div class="targetbar">

      % if target:
        <div class="reply">
          <img width="30" src="${target["sender"]["image"]}" />
          ${act(action).format(target["sender"].get("name", "somebody"), user(target))}
        </div>
      % else:
        <div class="buttons">
          <div class="label">${_("Send with:")}</div>
          % for account in accounts:
            <div class="account"
                 bgcolor="${account['color']}"
                 id="${account['_id']}"
                 style="${accountcss(account)}"
                 enabled="${str(account['send_enabled']).lower()}">
              % if account["send_enabled"]:
                <img class="icon" title="${act('title').format(account['protocol'], account['username'])}" src="${breakdance(account['protocol'])}" />
              % else:
                <img class="icon" title="${act('disabledtitle').format(account['protocol'], account['username'])}" src="${breakdance(account['protocol'])}" />
              % endif
            </div>
          % endfor
        </div>
      % endif
    </div>

  </body>
</html>
