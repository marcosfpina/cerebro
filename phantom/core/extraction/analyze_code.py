# scripts/02_analyze_code.py
"""
Análise hermética completa dos repositórios
- AST parsing
- Dependency graphs
- Documentation extraction
- Comment analysis
- Git history patterns
"""

from pathlib import Path
from typing import Dict, List
import ast
import tree_sitter
from tree_sitter_languages import get_language, get_parser
from dataclasses import dataclass, asdict
import json

@dataclass
class CodeArtifact:
    """Unidade atômica de conhecimento"""
    repo: str
    file_path: str
    artifact_type: str  # function, class, module, config, comment
    name: str
    content: str
    context: str  # código ao redor
    dependencies: List[str]
    documentation: str
    metadata: Dict

class HermeticAnalyzer:
    """Análise profunda e hermética de código"""

    def __init__(self):
        # Parsers pra múltiplas linguagens
        self.parsers = {
            'python': get_parser('python'),
            'nix': get_parser('nix'),
            'rust': get_parser('rust'),
            'typescript': get_parser('typescript'),
            'bash': get_parser('bash'),
        }

    def analyze_repo(self, repo_path: Path) -> List[CodeArtifact]:
        """Extrai TUDO de um repositório"""
        artifacts = []

        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                lang = self.detect_language(file_path)
                if lang in self.parsers:
                    artifacts.extend(
                        self.analyze_file(file_path, lang)
                    )

        return artifacts

    def analyze_file(self, file_path: Path, lang: str) -> List[CodeArtifact]:
        """Análise profunda de um arquivo"""
        content = file_path.read_text(errors='ignore')
        parser = self.parsers[lang]
        tree = parser.parse(bytes(content, 'utf8'))

        artifacts = []

        if lang == 'python':
            artifacts.extend(self.analyze_python(file_path, content, tree))
        elif lang == 'nix':
            artifacts.extend(self.analyze_nix(file_path, content, tree))
        # ... outros langs

        return artifacts

    def analyze_python(self, file_path: Path, content: str, tree) -> List[CodeArtifact]:
        """Análise específica de Python"""
        artifacts = []

        # Parse AST
        try:
            ast_tree = ast.parse(content)
        except:
            return artifacts

        # Extrai funções
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                artifacts.append(CodeArtifact(
                    repo=str(file_path.parent.parent.name),
                    file_path=str(file_path),
                    artifact_type='function',
                    name=node.name,
                    content=ast.get_source_segment(content, node),
                    context=self.get_context(content, node.lineno),
                    dependencies=self.extract_dependencies(node),
                    documentation=ast.get_docstring(node) or "",
                    metadata={
                        'line_number': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                    }
                ))

            # Classes
            elif isinstance(node, ast.ClassDef):
                artifacts.append(CodeArtifact(
                    repo=str(file_path.parent.parent.name),
                    file_path=str(file_path),
                    artifact_type='class',
                    name=node.name,
                    content=ast.get_source_segment(content, node),
                    context=self.get_context(content, node.lineno),
                    dependencies=self.extract_class_dependencies(node),
                    documentation=ast.get_docstring(node) or "",
                    metadata={
                        'line_number': node.lineno,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        'bases': [b.id for b in node.bases if isinstance(b, ast.Name)],
                    }
                ))

        # Extrai comentários significativos
        artifacts.extend(self.extract_comments(file_path, content))

        return artifacts

    def analyze_nix(self, file_path: Path, content: str, tree) -> List[CodeArtifact]:
        """Análise específica de Nix - SUPER IMPORTANTE pro teu caso!"""
        artifacts = []

        # Extrai derivations
        derivations = self.extract_nix_derivations(tree)
        for deriv in derivations:
            artifacts.append(CodeArtifact(
                repo=str(file_path.parent.parent.name),
                file_path=str(file_path),
                artifact_type='nix_derivation',
                name=deriv['name'],
                content=deriv['content'],
                context=content,  # todo o flake como contexto
                dependencies=deriv['build_inputs'],
                documentation=self.extract_nix_docs(deriv),
                metadata={
                    'type': deriv['type'],  # mkDerivation, buildPythonPackage, etc
                    'outputs': deriv.get('outputs', ['out']),
                    'system': deriv.get('system'),
                }
            ))

        # Extrai módulos NixOS
        modules = self.extract_nixos_modules(tree)
        for mod in modules:
            artifacts.append(CodeArtifact(
                repo=str(file_path.parent.parent.name),
                file_path=str(file_path),
                artifact_type='nixos_module',
                name=mod['name'],
                content=mod['content'],
                context=content,
                dependencies=mod['imports'],
                documentation=mod.get('description', ''),
                metadata={
                    'options': mod.get('options', []),
                    'config': mod.get('config', {}),
                }
            ))

        return artifacts

    def extract_comments(self, file_path: Path, content: str) -> List[CodeArtifact]:
        """Extrai comentários significativos (não triviais)"""
        artifacts = []

        # Regex pra comentários multi-linha, TODOs, FIXMEs, etc
        import re

        # TODO comments
        todos = re.findall(r'#\s*(TODO|FIXME|HACK|NOTE):\s*(.+)', content)
        for tag, comment in todos:
            artifacts.append(CodeArtifact(
                repo=str(file_path.parent.parent.name),
                file_path=str(file_path),
                artifact_type='comment_todo',
                name=f"{tag}",
                content=comment,
                context="",
                dependencies=[],
                documentation="",
                metadata={'tag': tag}
            ))

        return artifacts

    def get_context(self, content: str, line_num: int, window: int = 5) -> str:
        """Pega linhas ao redor pra contexto"""
        lines = content.split('\n')
        start = max(0, line_num - window)
        end = min(len(lines), line_num + window)
        return '\n'.join(lines[start:end])

    def extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Extrai dependencies de uma função"""
        deps = set()

        for child in ast.walk(node):
            # Imports
            if isinstance(child, ast.Import):
                for alias in child.names:
                    deps.add(alias.name)
            elif isinstance(child, ast.ImportFrom):
                deps.add(child.module)

            # Function calls
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    deps.add(child.func.id)

        return list(deps)

def main():
    analyzer = HermeticAnalyzer()

    repos_dir = Path("./repos")
    output_dir = Path("./data/analyzed")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_artifacts = []

    for repo_path in repos_dir.iterdir():
        if repo_path.is_dir():
            print(f"📊 Analyzing {repo_path.name}...")
            artifacts = analyzer.analyze_repo(repo_path)
            all_artifacts.extend(artifacts)

            # Save per-repo
            repo_output = output_dir / f"{repo_path.name}.json"
            with open(repo_output, 'w') as f:
                json.dump(
                    [asdict(a) for a in artifacts],
                    f,
                    indent=2
                )

    print(f"✅ Analyzed {len(all_artifacts)} artifacts total")

# Save combined (JSONL Otimizado para Vertex AI Search)
    print(f"💾 Salvando como JSONL para Ingestão no GCP...")
    jsonl_path = output_dir / "all_artifacts.jsonl"

    with open(jsonl_path, 'w') as f:
        for artifact in all_artifacts:
            # Estrutura 'Document' exigida pelo Discovery Engine
            doc = {
                "id": f"{artifact.repo}-{artifact.name}".replace("/", "-"), # IDs seguros
                "structData": {
                    "repo": artifact.repo,
                    "type": artifact.artifact_type,
                    "line_number": artifact.metadata.get('line_number'),
                    # Adicione aqui qualquer metadado que você queira filtrar depois
                },
                "content": {
                    "mimeType": "text/plain",
                    "uri": artifact.file_path,
                    # O 'rawBytes' precisa ser base64 string se for binário,
                    # mas para text/plain, o campo 'data' ou texto direto costuma funcionar melhor
                    # dependendo da versão da API. O formato abaixo é seguro para JSONL GCS:
                }
            }

            # Truque: A API de ingestão via GCS as vezes prefere que o conteúdo esteja inline
            # ou que seja um 'structData' rico.
            # Para texto puro, podemos injetar o conteúdo no structData para garantir indexação
            # ou usar o campo 'jsonData' (que vira string pesquisável).

            # Versão simplificada que funciona bem:
            final_doc = {
                "id": doc["id"],
                "jsonData": json.dumps({
                    "title": artifact.name,
                    "url": artifact.file_path,
                    "content": artifact.content, # O texto do código vai aqui
                    "repo": artifact.repo,
                    "context": artifact.context
                })
            }

            f.write(json.dumps(final_doc) + '\n')

    print(f"✅ Arquivo pronto para upload: {jsonl_path}")
    print(f"   Comando sugerido: gcloud storage cp {jsonl_path} gs://SEU_BUCKET/")

if __name__ == "__main__":
    main()
