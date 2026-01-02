import os
import sys
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.exceptions import GoogleAPICallError

# Carrega as variáveis do arquivo .env
load_dotenv()

def get_env_var(var_name):
    value = os.getenv(var_name)
    if not value or value.startswith("seu-"):
        print(f"ERRO: A variável '{var_name}' não está configurada corretamente no .env")
        sys.exit(1)
    return value

def run_grounded_search():
    # Pega configurações
    project_id = get_env_var("GOOGLE_CLOUD_PROJECT_ID")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    model_id = os.getenv("GENAI_MODEL", "gemini-1.5-flash")
    query_text = os.getenv("SEARCH_QUERY", "O que é computação quântica?")

    print(f"🚀 Iniciando busca com Grounding no Google Search...")
    print(f"   Projeto: {project_id}")
    print(f"   Modelo: {model_id}")
    print(f"   Pergunta: {query_text}\n")

    try:
        client = discoveryengine.GroundedGenerationServiceClient()
        location_path = client.common_location_path(project=project_id, location=location)

        request = discoveryengine.GenerateGroundedContentRequest(
            location=location_path,
            generation_spec=discoveryengine.GenerateGroundedContentRequest.GenerationSpec(
                model_id=model_id,
            ),
            contents=[
                discoveryengine.GroundedGenerationContent(
                    role="user",
                    parts=[discoveryengine.GroundedGenerationContent.Part(text=query_text)]
                )
            ],
            grounding_spec=discoveryengine.GenerateGroundedContentRequest.GroundingSpec(
                grounding_sources=[
                    discoveryengine.GenerateGroundedContentRequest.GroundingSource(
                        google_search_source=discoveryengine.GenerateGroundedContentRequest.GroundingSource.GoogleSearchSource()
                    )
                ]
            )
        )

        response = client.generate_grounded_content(request)

        print("-" * 40)
        print("RESULTADO GERADO:")
        print("-" * 40)

        full_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                print(part.text, end="")
                full_text += part.text
        print("\n" + "-" * 40)

        # Mostra links de referência se houver
        if response.candidates and response.candidates[0].grounding_metadata.search_entry_point:
             print(f"\nVer mais no Google: {response.candidates[0].grounding_metadata.search_entry_point.rendered_content}")

    except GoogleAPICallError as e:
        print(f"\n❌ Erro na API do Google: {e.message}")
        if "PermissionDenied" in str(e):
            print("Dica: Verifique se você ativou a 'Discovery Engine API' e se logou com 'gcloud auth application-default login'.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    run_grounded_search()
