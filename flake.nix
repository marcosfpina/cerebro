{
  description = "GenAI Credit Validation Framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python customizado com todas as dependências
        pythonEnv = pkgs.python313.withPackages (ps: with ps; [
          # CLI dependencies
          typer
          rich
          pydantic
          python-dotenv
          tqdm

          # RAG/API dependencies
          fastapi
          uvicorn
          transformers
          torch
          chromadb

          # Pip para instalar pacotes GCP que não estão no nixpkgs
          pip
          setuptools
          wheel
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.google-cloud-sdk
            pkgs.zsh
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
          ];

          # ⚠️ ATENÇÃO: Edite estas variáveis com seus valores reais
          GOOGLE_CLOUD_PROJECT_ID = "gen-lang-client-0530325234";
          GOOGLE_CLOUD_LOCATION = "global";  # ou "us-central1" se preferir regional

          # DATA_STORE_ID vem do manage_datastores.py - deixe vazio por ora
          DATA_STORE_ID = "ds-app-v4-5e020c93";

          # Query de teste (pode ser sobrescrita com export SEARCH_QUERY="...")
          SEARCH_QUERY = "What is Vertex AI Search?";

          shellHook = ''
            # LD_LIBRARY_PATH para libs do sistema
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
            ]}:$LD_LIBRARY_PATH"

            # PYTHONPATH para imports corretos
            export PYTHONPATH="$PWD:$PYTHONPATH"

            # Instala dependências GCP em diretório local (via pip)
            export PIP_PREFIX="$PWD/.nix-pip"
            export PYTHONPATH="$PIP_PREFIX/${pythonEnv.sitePackages}:$PYTHONPATH"
            export PATH="$PIP_PREFIX/bin:$PATH"

            if [ ! -d "$PIP_PREFIX" ]; then
              echo "📥 Instalando dependências GCP..."
              pip install --prefix="$PIP_PREFIX" --no-warn-script-location --quiet \
                google-cloud-discoveryengine \
                google-cloud-billing \
                google-cloud-storage \
                google-cloud-dialogflow-cx \
                google-cloud-bigquery \
                google-auth
              echo "✅ Dependências GCP instaladas"
            fi

            # Cerebro - Unified command interface
            cerebro() {
              case "$1" in
                # Info commands
                info|i)
                  python phantom.py info
                  ;;
                version|v)
                  python phantom.py version
                  ;;
                help|h)
                  python phantom.py --help
                  ;;

                # GCP operations
                auth|login)
                  gcloud auth application-default login
                  ;;
                validate|check)
                  python phantom.py gcp validate
                  ;;
                list|ls)
                  python phantom.py gcp datastores-list
                  ;;
                create)
                  shift
                  python phantom.py gcp datastores-create "$@"
                  ;;
                search|query|q)
                  shift
                  python phantom.py gcp search "$@"
                  ;;

                # Credit management
                loadtest|burn)
                  shift
                  python phantom.py credit loadtest "$@"
                  ;;
                audit|billing)
                  shift
                  python phantom.py credit audit "$@"
                  ;;
                dialogflow|df)
                  shift
                  python phantom.py credit dialogflow "$@"
                  ;;

                # Utilities
                status|config)
                  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                  echo "Project:    $GOOGLE_CLOUD_PROJECT_ID"
                  echo "Location:   $GOOGLE_CLOUD_LOCATION"
                  echo "DataStore:  $DATA_STORE_ID"
                  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                  ;;

                *)
                  echo "Usage: cerebro <command> [args]"
                  echo ""
                  echo "Commands:"
                  echo "  info, version, help     - Framework information"
                  echo "  auth                    - Authenticate with GCP"
                  echo "  validate                - Validate GCP setup"
                  echo "  list                    - List datastores"
                  echo "  create <id>             - Create datastore"
                  echo "  search <query>          - Search with AI"
                  echo "  loadtest                - Burn GenAI credits"
                  echo "  audit                   - Audit consumption"
                  echo "  dialogflow              - Burn Dialogflow credits"
                  echo "  status                  - Show current config"
                  ;;
              esac
            }

            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🧠 CEREBRO - Phantom Framework CLI"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "📋 COMANDOS:"
            echo ""
            echo "  cerebro info              Framework info"
            echo "  cerebro auth              Authenticate with GCP"
            echo "  cerebro validate          Validate GCP setup"
            echo "  cerebro list              List datastores"
            echo "  cerebro create <id>       Create datastore"
            echo "  cerebro search <query>    Search with AI"
            echo "  cerebro loadtest          Burn GenAI credits"
            echo "  cerebro audit             Audit consumption"
            echo "  cerebro status            Show current config"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "💡 Quick Start: cerebro validate → cerebro list → cerebro search 'test'"
            echo ""
          '';
        };
      }
    );
}
