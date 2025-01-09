javac -encoding UTF-8 -d myout ./src/*
jar -cvfm main.jar ./META-INF\MENIFEST.MF -C myout .