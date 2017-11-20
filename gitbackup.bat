set PATH=%PATH%;C:\Program Files\Git\bin;
git config core.autocrlf true
git add -A
git commit -m "backup"
git push -u origin master
git push -u origin2 master