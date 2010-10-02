<%
def breakdance(name, size=22):
  if tree or small_icons: size = 16
  return resources.get_ui_asset("icons/breakdance/%sx%s/%s.png" % (size, size, name))

def icon(name, size=24):
  if tree or small_icons: size = 16
  return resources.get_ui_asset("icons/streams/%sx%s/%s.png" % (size, size, name))

def active(item):
  if selected:
    return selected["account"] == item["account"] and \
           selected["stream"] == item["stream"] and \
           selected["transient"] == item["transient"]
%>

<%def name="gradient()" filter="trim">
  -webkit-gradient(linear, left top, right 100%, from(rgba(255, 255, 255, 0.6)), to(rgba(255, 255, 255, 0.6)))
</%def>

<%def name="shine()" filter="trim">
  -webkit-gradient(linear, left top, left bottom, from(rgba(0, 0, 0, 0.45)), to(rgba(255, 255, 255, 0.42)), color-stop(0.4, rgba(0, 0, 0, 0.15)), color-stop(0.6, rgba(0, 0, 0, 0.0)), color-stop(0.9, rgba(255, 255, 255, 0.06)))
</%def>

<%def name="convex()" filter="trim">
  -webkit-gradient(linear, left top, left bottom, from(rgba(255, 255, 255, 0.3)), to(rgba(255, 255, 255, 0.45)))
</%def>

<%def name="accountcss(account)" filter="trim">
  % if not tree:
  background: ${account["color"].hex} ${gradient()};
  %endif
</%def>

<%def name="bullet(img)" filter="trim">
  background-image: url(${img});
  background-repeat: no-repeat;
  padding-left: 22px;
  background-position: 0 0;
  vertical-align:top;
</%def>

<html>
  <head>
    <script src="jquery.js"></script>
    <script>
      function selectstream(item) {
        $(".compact .stream").css({
            "background": "none",
            "border": "1px solid rgba(255,255,255,0)",
            "color": "${theme['text'].hex}",
        });

        item.css({
          % if tree:
            "background": "${theme['base_selected'].hex}",
            "color": "${theme['text_selected'].hex}",
          % else:
            "background": item.attr("bgcolor") + " ${convex()}",
            "border": "1px solid" + item.attr("bgcolor")
          % endif
        });
      }

      function generateStreamURL(item) {
        if (item.attr("transient")) return "gwibber:/stream?transient=" + item.attr("transient");
        else return "gwibber:/stream?account=" + item.attr("account") + "&stream=" + item.attr("stream");
      }

      $(document).ready(function() {
        selectstream($(".stream[active='True']"))

        $(".closebutton").click(function() {
            document.location = "gwibber:/close?transient=" + $(this).attr("transient");
            return false;
        });

        $(".compact .stream").click(function() {
            selectstream($(this));
            document.location = generateStreamURL($(this));
        });
      });
    </script>

    <style>
      body {
        % if not tree: 
          background: ${theme["bg"].hex};
        % else:
          background: ${theme["base"].hex};
        % endif
        
        margin: 0px;
        padding: 0px;
        -webkit-user-select: none;
      }

      img { 
        -webkit-user-drag: none;
      }

      .account, .searches {
        % if not tree:
        margin-top: 15px;
        -webkit-border-radius: 5px;
        % endif
      }

      .stream {
        border: 1px solid rgba(255,255,255,0);
        % if not tree:
          -webkit-border-radius: 5px;
        % endif
        padding-top: 3px;
        padding-bottom: 3px;
        cursor: default;
      }

      .icon {
        display: block;
        margin-left: auto;
        margin-right: auto;
        % if tree:
          float: left;
          padding-right: 5px;
        % endif
      }

      .closebutton {
        % if not tree:
          display: none;
        % endif

        float: right;
      }

      .navigation {
        padding: 0px;
        margin: 0px;
        width: 100%;
      }

      % if tree:
        .streams .stream {
          padding-left: 15px;
        }
      % endif

      .label {
        % if not tree:
          display: none;
        % endif

        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;
      }
    </style>
  </head>
  <body>
    <div class="compact navigation">
      % for item in streams:
        % if item["account"]:
          <div class="account"
               bgcolor="${item['color'].hex}"
               id="${item['account']}"
               style="${accountcss(item)}">

            <div class="stream"
                 active="${active(item)}"
                 account="${item['account']}"
                 stream="${item['stream']}"
                 bgcolor="${item['color'].hex}">

                <img class="icon" title="${item['protocol']} (${item['name']})" src="${breakdance(item['protocol'])}" />
                <div class="label">${item['name']}</div>
            </div>
              
            <div class="streams">
              % for stream in item["items"]:
                <div class="stream"
                     % if stream["transient"]:
                     transient="${stream['transient']}"
                     % endif
                     active="${active(stream)}"
                     account="${stream['account']}"
                     stream="${stream['stream']}"
                     bgcolor="${item['color'].hex}">

                  <img class="icon" title="${item['protocol']} (${item['name']}) - ${stream['name']}" src="${icon(stream['stream'])}" />
                  % if stream["transient"]:
                    <img class="closebutton" transient="${stream['transient']}" src="${resources.icon('gtk-close')}" />
                  % endif
                  <div class="label">${stream['name']}</div>
                </div>
              % endfor
            </div>

          </div>
        % elif item["stream"] == "search":

          <div class="searches">

            <div class="stream"
                 active="${active(item)}"
                 account="${item['account']}"
                 stream="${item['stream']}"
                 bgcolor="${theme['bg_selected'].hex}">

                <img class="icon" title="${item['stream']}" src="${icon(item['stream'])}" />
                <div class="label">${item['name']}</div>
            </div>

            <div class="streams">
              % for stream in item["items"]:
                <div class="stream search"
                     % if stream["transient"]:
                     transient="${stream['transient']}"
                     % endif
                     active="${active(stream)}"
                     account="${stream['account']}"
                     stream="${stream['stream']}"
                     bgcolor="${theme['bg_selected'].hex}">

                  <img class="icon" title="${stream['account']}" src="${icon(stream['stream'])}" />
                  % if stream["transient"]:
                    <img class="closebutton" transient="${stream['transient']}" src="${resources.icon('gtk-close')}" />
                  % endif
                  <div class="label">${stream['name']}</div>
                </div>
              % endfor
            </div>

        % else:
            
          <div class="stream"
               active="${active(item)}"
               account="${item['account']}"
               stream="${item['stream']}"
               bgcolor="${theme['bg_selected'].hex}">

              <img class="icon" title="${item['name']}" src="${icon(item['stream'])}" />
              <div class="label">${item['name']}</div>
          </div>

        % endif
      % endfor
    </div>

  </body>
</html>
