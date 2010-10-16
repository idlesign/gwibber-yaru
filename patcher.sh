#! /bin/bash

echo
echo 'This patcher brings Ya.ru protocol support into Gwibber.'
echo 'It will copy some files and monkeypatch others.'
echo 'NOTE: run it with sudo. NB: It is a one way ticket!'
echo
echo 'Press Ctrl+C now if you do not want a possible mess.'
echo

read bounce

clear
cd `dirname $0`

echo
echo 'Copying files...'

cp -pv ui/gwibber-accounts-yaru.ui /usr/share/gwibber/ui/gwibber-accounts-yaru.ui
cp -pv ui/icons/breakdance/16x16/yaru.png /usr/share/gwibber/ui/icons/breakdance/16x16/yaru.png
cp -pv gwibber/lib/gtk/yaru.py /usr/lib/python2.6/dist-packages/gwibber/lib/gtk/yaru.py
cp -pv gwibber/microblog/yaru.py /usr/lib/python2.6/dist-packages/gwibber/microblog/yaru.py

echo
echo 'Patching now...'

FILE_GTK='/usr/lib/python2.6/dist-packages/gwibber/lib/gtk/__init__.py'
FILE_GTK_SEARCH='__all__ = \['
FILE_GTK_REPLACE='__all__ = \[\"yaru\", '

FILE_DISPATCHER='/usr/lib/python2.6/dist-packages/gwibber/microblog/dispatcher.py'
FILE_DISPATCHER_SEARCH_1='import twitter,'
FILE_DISPATCHER_REPLACE_1='import yaru, twitter,'
FILE_DISPATCHER_SEARCH_2='\"twitter\": twitter,'
FILE_DISPATCHER_REPLACE_2='\"twitter\": twitter,\n  \"yaru\": yaru,'

echo 'File: '$FILE_GTK
if grep yaru $FILE_GTK >/dev/null 2>&1; then
  echo '   -> Already patched.'
else
  if sed -i "s#$FILE_GTK_SEARCH#$FILE_GTK_REPLACE#g" $FILE_GTK >/dev/null 2>&1; then
    echo '   -> Patched.'
  else
    echo '   -> Patch failed :('
  fi
fi

echo 'File: '$FILE_DISPATCHER
if grep yaru $FILE_DISPATCHER >/dev/null 2>&1; then
  echo '   -> Already patched.'
else
  if sed -i "s#$FILE_DISPATCHER_SEARCH_1#$FILE_DISPATCHER_REPLACE_1#g" $FILE_DISPATCHER >/dev/null 2>&1; then
    echo '   -> Patched #1.'
  else
    echo '   -> Patch #1 failed :('
  fi
  if sed -i "s#$FILE_DISPATCHER_SEARCH_2#$FILE_DISPATCHER_REPLACE_2#g" $FILE_DISPATCHER >/dev/null 2>&1; then
    echo '   -> Patched #2.'
  else
    echo '   -> Patch #2 failed :('
  fi
fi

echo
echo 'The End'
