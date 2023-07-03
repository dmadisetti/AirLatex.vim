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
      in
      {
        # A Nix environment with your specified packages
        # Cache Bust!
        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.neovim python pkgs.sqlite ];
        };

        # let g:python3_host_prog = '/home/dylan/air/bin/python3'
        packages = rec {
          airlatex = pkgs.writeShellScriptBin "airlatex" ''
            PATH=$PATH:${pkgs.sqlite}/bin ${pkgs.neovim}/bin/nvim \
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
          default = airlatex;
        };
      });
}
