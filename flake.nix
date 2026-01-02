{
  description = "Ambiente GenAI Plug-n-Play";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python313.withPackages (ps: with ps; [
          google-cloud-discoveryengine
          python-dotenv
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.google-cloud-sdk # Inclui o gcloud CLI automaticamente
          ];

          shellHook = ''
            echo "🚀 Ambiente GenAI carregado!"
            echo "1. Edite o arquivo .env"
            echo "2. Faça login se precisar: gcloud auth application-default login"
            echo "3. Rode: python main.py"
          '';
        };
      }
    );
}  1
