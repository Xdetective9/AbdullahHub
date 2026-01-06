{ pkgs }: {
  deps = [
    pkgs.python39
    pkgs.python39Packages.pip
    pkgs.postgresql
    pkgs.nodejs-18_x
    pkgs.redis
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
    ];
    PYTHONBIN = "${pkgs.python39}/bin/python3.9";
    LANG = "en_US.UTF-8";
  };
}
