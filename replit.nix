{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.google-chrome
    pkgs.chromedriver
    pkgs.glib
    pkgs.libnss
    pkgs.alsa-lib
    pkgs.gtk3
    pkgs.xdg-utils
    pkgs.libxshmfence
    pkgs.libdrm
  ];
}
