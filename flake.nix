{
  description = "AirLatex as Hermetic package";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        python = pkgs.python310.withPackages (ps: with ps; [
          # Python packages from PyPI
          tornado
          requests
          pynvim
          intervaltree
          beautifulsoup4
          pybtex
        ]);
        remote = pkgs.runCommand "remote.vim" { } ''
          ${python}/bin/python3.10 ${./export.py} ${./.} airlatex > $out
        '';
        firefox-extension = pkgs.stdenv.mkDerivation rec {
          name = "firefox-extension";
          src = ./firefox;

          postPatch = ''
            # Patch the Python script headers
            ls -laR
            sed -i '1s,#!/usr/bin/env python,#!${python}/bin/python3.10,' ./app/bridge.py
            ${pkgs.jq}/bin/jq ".path = \"$out/app/bridge.py\"" ./app/bridge.json > ./app/tmp.json
            mv ./app/tmp.json ./app/bridge.json
          '';

          installPhase = ''
            mkdir -p $out
            cp -r ./* $out/
          '';
        };
        airmount = pkgs.writers.writePython3Bin "airmount"
          {
            libraries = with
              pkgs.python3Packages; [ pynvim fuse requests ];
          } ./fs.py;
        airlatexmk = pkgs.writers.writePython3Bin "airlatexmk"
          {
            libraries = with
              pkgs.python3Packages; [ pynvim ];
          } ./compile.py;

      in
      {
        # A Nix environment with your specified packages
        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.neovim python pkgs.sqlite airmount airlatexmk ];
        };

        # let g:python3_host_prog = '/home/dylan/air/bin/python3'
        packages = rec {
          inherit airmount airlatexmk;
          airlatex = pkgs.writeShellScriptBin "airlatex" ''
            BASE=/run/user/$(id -u)/airlatex
            mkdir -p $BASE/builds

            VIMTEX_OUTPUT_DIRECTORY=$BASE/active \
            PATH=$PATH:${pkgs.sqlite}/bin:${airmount}/bin:${airlatexmk}/bin nvim \
                --listen $BASE/socket \
                -c "let g:python3_host_prog='${python}/bin/python3.10'" \
                -c "set runtimepath+=${./.}" \
                -c "source ${remote}" \
                -c AirLatex
          '';
          extension = pkgs.writeShellScriptBin "extension" ''
            # Cachbust=1
            mkdir -p ~/.mozilla/native-messaging-hosts
            ln -sf ${firefox-extension}/app/bridge.json ~/.mozilla/native-messaging-hosts/airlatex.json
            cleanup() {
              rm ~/.mozilla/native-messaging-hosts/airlatex.json
            }
            trap cleanup EXIT
            ${airlatex}/bin/airlatex
          '';
          _addon = pkgs.writeShellScriptBin "extension" ''
            cd firefox/add-on
            ${pkgs.zip}/bin/zip -r ../../addon.xpi .
          '';
          default = airlatex;
        };
      });
}
