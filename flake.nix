{
  description = "A self-improving AI agent based on pi-coding-agent";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      home-manager,
    }:
    let
      eachSystem = flake-utils.lib.eachDefaultSystem (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          packages.default = pkgs.buildNpmPackage.override { nodejs = pkgs.nodejs_24; } {
            pname = "dude-chess";
            version = "0.1.0";
            src = ./.;
            npmDepsHash = "sha256-3jMZB08mQcIk/wdgmcbmgjNhhfdlWqQuF4AJl3F8sE8=";
            dontNpmBuild = true;
            postInstall = ''
              cp .opvars $out/.opvars
            '';
          };

          packages.skills = pkgs.stdenv.mkDerivation {
            pname = "dude-skills";
            version = "0.1.0";
            src = ./.pi/skills;
            buildInputs = [ pkgs.nodejs_24 pkgs.coreutils ];
            nativeBuildInputs = [ pkgs.makeWrapper ];
            phases = [ "unpackPhase" "buildPhase" "installPhase" ];
            buildPhase = ''
              # Install npm dependencies for skills that have package.json
              find $src -maxdepth 2 -name "package.json" -type f | while read pkg; do
                skill_dir=$(dirname "$pkg")
                if [ -f "$skill_dir/package-lock.json" ]; then
                  echo "Installing locked npm dependencies for $skill_dir..."
                  (cd "$skill_dir" && npm ci --prefer-offline --no-audit --progress=false 2>/dev/null || true)
                else
                  echo "Installing npm dependencies for $skill_dir (no lockfile)..."
                  (cd "$skill_dir" && npm install --prefer-offline --no-audit --progress=false 2>/dev/null || true)
                fi
              done
            '';
            installPhase = ''
              mkdir -p $out/skills
              cp -r * $out/skills/
            '';
          };

          devShells.default = pkgs.mkShell {
            buildInputs = with pkgs; [
              nodejs_24
              git
              gh
              google-cloud-sdk
              _1password-cli
              chromium
            ];
            shellHook = ''
              export PATH=$PWD/node_modules/.bin:$PATH
              export PI_SKILLS=${self.packages.${system}.skills}/skills
              export WEB_BROWSE_BROWSER_BIN=${pkgs.chromium}/bin/chromium
            '';
          };
        }
      );
    in
    eachSystem
    // {
      # Home Manager Module for the Systemd Service
      homeManagerModules.dude-chess =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        {
          options.services.dude-chess = {
            enable = lib.mkEnableOption "Dude Chess Agent Service";
            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.system}.default;
            };
            workingDirectory = lib.mkOption {
              type = lib.types.str;
              default = "${config.home.homeDirectory}/dude-workspace/dude-chess";
            };
            configDirectory = lib.mkOption {
              type = lib.types.str;
              default = "${config.home.homeDirectory}/.config/dude-chess";
            };
          };

          options.services.dude-chess-checker = {
            enable = lib.mkEnableOption "Dude Chess Checker Service (Daily Lichess Check)";
            lichessUsername = lib.mkOption {
              type = lib.types.str;
              description = "Lichess username to check for new games.";
            };
            interval = lib.mkOption {
              type = lib.types.str;
              default = "daily";
              description = "Systemd calendar expression for how often to check for new games.";
            };
            workingDirectory = lib.mkOption {
              type = lib.types.str;
              default = "${config.home.homeDirectory}/dude-workspace/dude-chess";
            };
            configDirectory = lib.mkOption {
              type = lib.types.str;
              default = "${config.home.homeDirectory}/.config/dude-chess";
            };
          };

          config = {
            systemd.user.services.dude-chess = lib.mkIf config.services.dude-chess.enable {
              Unit = {
                Description = "Dude Chess AI Agent";
                After = [ "network.target" ];
                StartLimitBurst = "5";
                StartLimitIntervalSec = "120s";
              };
              Service = {
                Type = "simple";
                WorkingDirectory = config.services.dude-chess.workingDirectory;
                ExecStartPre = [
                  "${pkgs.coreutils}/bin/mkdir -p ${config.services.dude-chess.configDirectory}"
                  "${pkgs._1password-cli}/bin/op run --env-file ${config.services.dude-chess.package}/.opvars -- /usr/bin/bash -c \"[ -z \"$GEMINI_JSON_TOKEN\" ] || echo \"$GEMINI_JSON_TOKEN\" > ~/.pi/agent/auth.json\""
                ];
                ExecStart = "${pkgs._1password-cli}/bin/op run --env-file ${config.services.dude-chess.package}/.opvars -- ${config.services.dude-chess.package}/bin/dude-chess";
                Restart = "always";
                RestartSec = "5s";
                Environment = [
                  "DUDE_CONFIG_DIR=${config.services.dude-chess.configDirectory}"
                  "PI_SKILLS=${self.packages.${pkgs.system}.skills}/skills"
                  "WEB_BROWSE_BROWSER_BIN=${pkgs.chromium}/bin/chromium"
                  "PATH=${
                    lib.makeBinPath [
                      pkgs.git
                      pkgs.gh
                      pkgs.google-cloud-sdk
                      pkgs.nodejs_24
                      pkgs._1password-cli
                      pkgs.chromium
                      pkgs.coreutils
                    ]
                  }:${config.services.dude-chess.package}/lib/node_modules/dude-chess/node_modules/.bin:/usr/bin:/bin"
                ];
                EnvironmentFile = [
                  "-${config.services.dude-chess.workingDirectory}/.env"
                  "-${config.services.dude-chess.configDirectory}/.env"
                ];
              };
              Install.WantedBy = [ "default.target" ];
            };

            systemd.user.services.dude-chess-checker = lib.mkIf config.services.dude-chess-checker.enable {
              Unit = {
                Description = "Dude Chess Checker - New Lichess Games";
                After = [ "network.target" ];
              };
              Service = {
                Type = "oneshot";
                WorkingDirectory = config.services.dude-chess-checker.workingDirectory;
                ExecStart = "${pkgs._1password-cli}/bin/op run --env-file ${self.packages.${pkgs.system}.default}/.opvars -- ${pkgs.nodejs_24}/bin/node src/daily-check.js";
                Environment = [
                  "DUDE_CONFIG_DIR=${config.services.dude-chess-checker.configDirectory}"
                  "LICHESS_USERNAME=${config.services.dude-chess-checker.lichessUsername}"
                  "PATH=${
                    lib.makeBinPath [
                      pkgs.nodejs_24
                      pkgs._1password-cli
                    ]
                  }:/usr/bin:/bin"
                ];
                EnvironmentFile = [
                  "-${config.services.dude-chess-checker.workingDirectory}/.env"
                  "-${config.services.dude-chess-checker.configDirectory}/.env"
                ];
              };
            };

            systemd.user.timers.dude-chess-checker = lib.mkIf config.services.dude-chess-checker.enable {
              Unit = {
                Description = "Run Dude Chess Checker Periodically";
              };
              Timer = {
                OnCalendar = config.services.dude-chess-checker.interval;
                Persistent = true;
              };
              Install.WantedBy = [ "timers.target" ];
            };
          };
        };
    };
}
