<%def name="map(lat, long, w=175, h=80, maptype='mobile')">
  <a href="http://maps.google.com/maps?q=${lat},${long}">
    <img src="http://maps.google.com/staticmap?zoom=12&size=${w}x${h}&maptype=${maptype}&markers=${lat},${long}" />
  </a>
</%def>

<%def name="profile_url(data)" filter="trim">
  % if "user_messages" in services[data["protocol"]]["features"]:
    gwibber:/user?acct=${data["account"]}&amp;name=${data["sender"]["nick"]}
  % else:
    ${data['sender']['url']}
  % endif
</%def>

<%def name="comment(data)">
  <p><a href="${data["sender"]["url"]}">${data["sender"]["name"]}</a>: ${data['text']}</p>
</%def>

<%def name="msgclass(data, classes=['unread', 'reply', 'private'])">
  <% return " ".join(i for i in classes \
    if hasattr(data, "is_" + i) and getattr(data, "is_" + i)) %>
</%def>

<%def name="msgstyle(data)" filter="trim">
</%def>

<%def name="geo_position(data)">
  <div class="position">
    % if hasattr(data, "location_name"):
      <p class="location">_("Posted from: ${data.location_name}")</p>
    % endif
    ${self.map(*data.geo_position)}
  </div>
</%def>

<%def name="liked_by(data)">
  <p class="likes">_("${data.liked_by} user(s) liked this")</p> 
</%def>

<%def name="comments(data)">
  <div class="comments">
    % for c in data["comments"][-3:]:
      ${self.comment(c)}
    % endfor
  </div>
</%def>

<%def name="image(data)">
  <a href="${profile_url(data)}">
    <div class="imgbox" title="${data["sender"].get("nick", "")}" style="background-image: url(${data["sender"]["image"]});"></div>
  </a>
</%def>

<%def name="images(data)">
  <div class="thumbnails">
    % for i in data["images"]:
      <a href="${i['url']}"><img src="${i.get('src', 0) or i.get('src', 0)}" /></a>
    % endfor
  </div>
</%def>

<%def name="dupes(data)">
  % if "dupes" in data and len(data['dupes']) > 0:
    <div class="dupes">
      % for d in data['dupes']:
        ${self.message(d)}
      % endfor
    </div>
  % endif
</%def>

<%def name="buttons(data)">
  <div class="buttonitem">
    <a href="gwibber:/menu?msg=${data['_id']}"><img width="16px" src="${resources.icon('system-run')}" /></a> 
  </div>
  <div class="buttonitem">
    <a href="gwibber:/reply?msg=${data['_id']}"><img width="16px" src="${resources.icon('mail-reply-sender')}" /></a>
  </div>
</%def>

<%def name="extended_text(data)">
  <p class="text">${data.extended_text}</p>
</%def>

<%def name="fold(data, ops=['geo_position', 'liked_by', 'comments', 'extended_text', 'images'])">
  <div class="fold">
    % for o in ops:
      % if data.get(o, 0):
        ${getattr(self, o)(data)}
      % endif
    % endfor
  </div>
</%def>
  
<%def name="timestring(data)" filter="trim">
  <a href="gwibber:/read?msg=${data['_id']}">${data['time_string']}</a>
  % if data.get("source", 0):
    <a>${_("from")} ${data["source"]}</a>
  % endif
  % if data.get("reply", {}).get("nick", 0):
    <a href="${data['reply'].get('url', '#')}">${_("in reply to")} ${data['reply']['nick']}</a>
  % endif
</%def>

<%def name="sender(data)" filter="trim">
  % if preferences["show_fullname"]:
    ${data['sender'].get("name", 0) or data["sender"].get("nick", "")}
  % else:
    ${data['sender'].get("nick", 0) or data["sender"].get("name", "")}
  % endif
</%def>

<%def name="title(data)">
  <span class="title">${data['title'] if "title" in data else sender(data)}</span>
</%def>

<%def name="sigil(data)">
  <span class="sigil">
    <img src="${resources.get_ui_asset('icons/breakdance/16x16/%s.png' % data['protocol'])}" />
  % if data.get("sigil", 0):
    <img src="${data['sigil']}" />
  % endif

  % if data.get("private", 0):
    <img src="${resources.get_ui_asset('icons/streams/16x16/private.png')}" />
  % endif
  </span>
</%def>

<%def name="content(data)">
  <p class="content">
    ${sigil(data)}   
    ${title(data)}
    <span class="time"> (${timestring(data)})</span><br />
  % if data.get("rtl", False):
    <span class="text rtl">${data.get('content', '')}</span>
  % else:
    <span class="text">${data.get('content', '')}</span>
  % endif
  </p>
</%def>

<%def name="sidebar(data)">
  % if "image" in data["sender"]:
    ${self.image(data)}
  % endif
</%def>

<%def name="messagebox(data)">
  <div id="${data["_id"]}" style="${self.msgstyle(data)}" class="message ${self.msgclass(data)}">
    ${caller.body()}
  </div>
</%def>

<%def name="user_header_message(data)">
  <%call expr="messagebox(data)">
    <center>
      <p class="content">
        <span class="title">${data.sender}</span><br />
        % if hasattr(data, "sender_followers_count"):
          <span class="text">_("${data.sender_followers_count} followers")</span><br />
          <span class="text">${data.sender_location}</span><br />
        % endif
        <span class="text"><a href="${data.external_profile_url}">${data.external_profile_url}</a></span>
      </p>
    </center>
  </%call>
</%def>

<%def name="toggledupe(data)">
  % if "dupes" in data and len(data["dupes"]) > 0:
    <div class="buttonitem toggledupe"><img src="${resources.icon('list-add')}" /></div>
  % endif
</%def>

<%def name="message(data)">
  <div class="basemsg">
    <%call expr="messagebox(data)">
      <table cellspacing="0" cellpadding="0">
        <tr>
          <td>
            ${self.sidebar(data)}
          </td>
          <td width="100%">
            ${self.content(data)}
            ${self.fold(data)}
          </td>
          <td class="buttons">
            ${toggledupe(data)}
            <div class="hidden">
            ${self.buttons(data)}
            </div>
          </td>
        </tr>
      </table>
      
      ${self.dupes(data)}
    </%call>
  </div>
</%def>

<%def name="messages(data)">
  <div class="header">
  </div>
  <div class="messages">
    % for m in data:
      % if not m["is_dupe"]:
        ${self.message(m)}
      % endif
    % endfor
  </div>
  % if count and count < total:
    <div class="viewmore">
      <p><a href="gwibber:/more">_("View More Messages")</a></p>
    </div>
  % endif
</%def>

<%def name="accounts_list(accounts)">
  <table class="accounts">
    <thead><tr><td colspan="100%">_("Your Accounts")</td></tr></thead>
    % for a in accounts:
      <tr>
        <td>${a["username"]}</td>
        <td>
          <img src="${resources.get_ui_asset('icons/breakdance/16x16/%s.png' % a['protocol'])}" />
          ${protocols[a["protocol"]]["name"]}
        </td>
        <td>
          <a href="gwibber:/account?id=${a['id']}"><img src="${resources.icon('gtk-edit')}" /></a>
          <a href="gwibber:/account?id=${a['id']}&action=delete"><img src="${resources.icon('gtk-delete')}" /></a>
        </td>
      </tr>
    % endfor
  </table>
</%def>

<%def name="account_creation(accounts)">
  <div class="content_box account_creation">
    <div class="header">_("Create New Account")</div>
    % for p in ["twitter", "identica", "facebook", "friendfeed"]:
      <div class="block">
        <a href="gwibber:/account?id=${p}&action=create"><img src="${resources.get_ui_asset('icons/32x32/%s.png' % p)}" /></a>
        <br />${protocols[p]["name"]}
      </div>
    % endfor
  </div>
</%def>

<%def name="latest_messages(messages)">
  <div class="content_box">
    <div class="header">_("Latest Replies")</div>
    <div class="box_content">
      <hr />
      % for m in messages:
        <p>
          <b>${m.sender}</b> <small>(${m.time_string})</small><br />
          ${m.html_string}
        </p>
        <hr />
      % endfor
    </div>
  </div>
</%def>

<%def name="errors(data)">
  % for e in data:
    <div class="content_box">
      <div class="header">
        <img style="float: left; padding-right: 5px;" src="${resources.icon('gtk-dialog-warning', use_theme=False)}" />
        ${e['error']}
        <div class="toggledupe"><img src="${resources.icon('list-add')}" /></div>
      </div>
      <div class="box_content">
        <code>${e['op']['opname']}</code> failed with <code>${e['type']}</code> on ${e['op']['protocol']} ${e['time_string']}
        <div class="dupes">
          <pre style="font-size: small">
            ${e["traceback"]}
          </pre>
        </div>
      </div>
    </div>
    <br />
  % endfor
</%def>


