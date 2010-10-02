body {
  word-break: break-word;
  font-family: Sans-serif;
  margin: 4px;
}

a {
  color: ${theme["bg_selected"].darker(.65).hex};
  text-decoration: none;
}

.time a { color: ${theme["bg_selected"].darker(.65).hex};}
a:hover { text-decoration: underline; }


td { vertical-align: top; }

p { line-height: 125% }

.basemsg .message {
  padding: 5px;
  padding-right: 0px;
  margin-bottom: 5px;
  -webkit-border-radius: 7px;
  display: block;
  border: 1px solid #aaa; 
}

.content {
  margin-top: 0px;
  color: ${theme['fg'].hex};
}

.title {
  font-size: 105%;
  font-weight: bold;
}

.time a {
  text-decoration: none;
  font-size: 80%;
}

.imgbox {
  width: 48px;
  height: 48px;
  margin-right: 6px;
  margin-top: 1px;

  -webkit-background-size: 100% 100%;
  background-image: url('');
  background-repeat: no-repeat;
  -webkit-border-radius: 5px;
}

.inlinenick {
  text-decoration: none;
  font-weight: bold;       
}

.messages h1 {
  text-align: center;
}

.buttons {
  width: 20px;
  padding-right: 5px;
}

.buttonitem {
  padding: 3px;
  display: inline-block;
}

.toggledupe {
  align: top;
}

.hidden {
  visibility: hidden;
}

.unread {
  border: 2px solid #888;
}

.reply {
  border: 2px solid #777;
}

.private {
  border: 2px solid #777;
}

.dupes {
  display: none;
  margin-top: 10px;
  margin-right: 5px;
}

.fold {
}

.fold a {
  text-decoration: none;
}

.accounts {
  border: 3px solid ${theme["bg_selected"].hex};
  -webkit-border-radius: 5px;
  color: ${theme["fg"].hex};
  vertical-align: middle;
  border-spacing: 0px;
  width: 100%;
}

.accounts a {
  text-decoration: none;
}

.accounts a:hover {
  text-decoration: underline;
}

.accounts td {
  padding: 5px;
  vertical-align: middle;
}

.accounts tr:nth-child(even) {
  background: ${theme["bg"].hex}
}

.accounts tr:nth-child(odd) {
  background: ${theme["bg"].darker(.90).hex};
}

.accounts tr:hover {
  background: -webkit-gradient(linear, left top, left bottom,
      from(${theme["bg_selected"].hex}),
      to(${theme["bg_selected"].darker(.90).hex}));
  color: ${theme["text_selected"].hex};
}

.accounts thead tr, .account_creation thead tr {
  background: -webkit-gradient(linear, left top, left bottom,
      from(${theme["bg_selected"].hex}),
      to(${theme["bg_selected"].darker(.80).hex})) !important;
  color: ${theme["text_selected"].hex};
  font-weight: bold;
}

.welcome {
  border: 3px solid ${theme["bg_selected"].hex};
  -webkit-border-radius: 5px;
  background: -webkit-gradient(linear, left top, left bottom,
      from(${theme["bg_selected"].hex}),
      to(${theme["bg_selected"].darker(.80).hex}));
  color: ${theme["text_selected"].hex};
  text-align: center;
  margin-bottom: 5px;
}

.content_box .header {
  background: -webkit-gradient(linear, left top, left bottom,
      from(${theme["bg_selected"].hex}),
      to(${theme["bg_selected"].darker(.80).hex})) !important;
  color: ${theme["text_selected"].hex};
  font-weight: bold;
  padding: 5px;
}

.content_box {
  border: 3px solid ${theme["bg_selected"].hex};
  -webkit-border-radius: 5px;
  color: ${theme["fg"].hex};
  vertical-align: middle;
  border-spacing: 0px;
  background: ${theme["bg"].hex};
}

.content_box .box_content {
  padding: 10px;
}

.account_creation .block {
  display: inline-block;
  padding: 5px;
  margin: 10px;
  text-align: center;
  border: 3px solid ${theme["bg"].hex};
  -webkit-border-radius: 5px;
}

.account_creation .block:hover {
  border: 3px solid ${theme["bg_selected"].hex};
  -webkit-border-radius: 5px;
  background: -webkit-gradient(linear, left top, left bottom,
      from(${theme["bg_selected"].hex}),
      to(${theme["bg_selected"].darker(.80).hex}));
  color: ${theme["text_selected"].hex};
}
