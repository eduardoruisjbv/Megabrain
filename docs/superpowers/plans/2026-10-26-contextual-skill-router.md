# Roteador de skills por contexto: plano de implementação

> **Para agentes de implementação:** Use `superpowers:executing-plans` ou `superpowers:subagent-driven-development` para executar este plano tarefa por tarefa. Marque cada passo com `[ ]` ao iniciar e `[x]` ao concluir.

**Objetivo:** Fazer o Megabrain selecionar skills instaladas em cada prompt e, em esforço alto, pesquisar e ativar uma skill externa temporariamente quando nenhuma skill local servir.

**Arquitetura:** Um módulo Python local indexa metadados e roteia prompts sem chamada adicional a um modelo. Adaptadores de hooks para Codex e Claude Code entregam o contexto escolhido. O instalador existente configura e remove esses hooks. Hermes mantém a seleção nativa atual.

**Tecnologias:** Python 3.8+, biblioteca padrão, Bash, JSON, hooks do Codex e Claude Code e CLI `skills` instalado a pedido do usuário.

**Especificação:** `docs/superpowers/specs/2026-10-26-contextual-skill-router-design.md`

## Restrições globais

- `low`, `minimal`, `medium` e esforço desconhecido usam apenas o índice local.
- `high`, `xhigh`, `max` e `ultra` permitem busca externa se nenhuma skill local atingir o limite.
- `auto` usa a política rápida.
- A substituição do Megabrain tem prioridade. Depois dela, o roteador lê valores documentados de ambiente ou configuração local.
- Se o esforço atual não puder ser confirmado, o roteador usa a política rápida.
- A busca externa analisa no máximo três resultados e espera no máximo 15 segundos, por padrão.
- A busca externa envia apenas termos de tópico redigidos, nunca o prompt completo ou dados do repositório.
- O roteador não instala skills externas permanentemente nem executa scripts de skills externas.
- Erros, timeout e respostas inválidas não bloqueiam o prompt do usuário.
- Codex e Claude Code recebem hooks de prompt. Hermes conserva a seleção nativa sem busca dinâmica.
- A configuração local fica em `$MB_HOME/state/skill-router.json`; o cache fica em `$MB_HOME/state/skill-router/`.
- O usuário autorizou atualizar o repositório remoto depois da verificação. Integrar a branch em `main` e enviar a alteração.

## Arquivos e responsabilidades

- Criar `lib/skill_router.py`: metadados, esforço, extração segura de tópicos, pontuação, catálogo, cache, protocolos dos hooks e configuração CLI.
- Modificar `lib/skills.py`: instalar, atualizar e remover hooks com o controle de propriedade atual.
- Modificar `install.sh`: disponibilizar o novo módulo na instalação local e remota, adicionar `megabrain skill-router` e instalar o CLI `skills` somente quando o usuário executar `setup-catalog`.
- Criar `tests/test_skill_router.py`: roteamento, esforço, redaction, catálogo, cache, falha aberta e contratos dos hooks.
- Modificar `tests/test_skills.py`: instalação idempotente, preservação de arquivos existentes e remoção dos hooks do Megabrain.
- Modificar `tests/test_hermes.py`: confirmar que Hermes não recebe hook dinâmico.
- Modificar `README.md`: explicar políticas, privacidade, configuração, dependência opcional e comandos.

## Focos de revisão

1. **Esforço ausente ou malformado:** deve usar a política rápida. Teste em `tests/test_skill_router.py::SkillRouterTest.test_override_and_unknown_effort_use_fast_policy`.
2. **Skill local fraca ou inexistente:** esforço médio não pode iniciar rede. Esforço alto pode consultar o catálogo. Testes `test_medium_skips_catalog_and_high_queries_only_below_local_threshold`.
3. **Prompt com dados privados:** termos enviados ao catálogo não podem conter caminhos, e-mails ou segredos. Teste `test_external_query_redacts_private_terms`.
4. **CLI ausente, lento ou inválido:** o hook deve terminar dentro do limite e liberar o prompt sem ativação externa. Teste `test_catalog_failure_fails_open`.
5. **Configuração preexistente ou editada pelo usuário:** instalar duas vezes não duplica hooks, e remover Megabrain preserva conteúdo não pertencente a ele. Testes em `tests/test_skills.py`.

---

### Tarefa 1: Roteamento local e política de esforço

**Arquivos:**
- Criar `lib/skill_router.py`
- Criar `tests/test_skill_router.py`

**Interfaces:**
- Produzir `SkillCandidate(name: str, description: str, path: Optional[Path], origin: str, activation_context: Optional[str])`.
- Produzir `RouteDecision(kind: str, candidates: List[SkillCandidate], reason: str)`, com `kind` igual a `local`, `external` ou `none`.
- Produzir `read_skills(roots: Iterable[Path]) -> List[SkillCandidate]`.
- Produzir `resolve_effort(client: str, override: Optional[str], environ: Mapping[str, str], home: Path) -> str`.
- Produzir `rank_skills(prompt: str, candidates: Sequence[SkillCandidate]) -> List[Tuple[float, SkillCandidate]]`.
- Produzir `select_local(prompt: str, candidates: Sequence[SkillCandidate], threshold: float) -> RouteDecision`.

- [x] **Passo 1: Criar testes locais que falham** para metadados válidos e inválidos, precedência da substituição, valores documentados de esforço, esforço desconhecido e pontuação de skills.
- [x] **Passo 2: Executar os testes e confirmar falha** com `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 3: Implementar as funções puras** em `lib/skill_router.py`. Usar `Installer.skill_roots` como origem de diretórios no adaptador, não duplicar a descoberta de raízes. Usar correspondência lexical ponderada sobre nome e descrição, com resultado entre `0.0` e `1.0`, limite padrão `0.5` e ativação de no máximo duas skills locais acima do limite.
- [x] **Passo 4: Executar os testes e confirmar sucesso** com `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 5: Criar commit local** `feat: add local contextual skill routing`.

### Tarefa 2: Busca externa temporária e cache

**Arquivos:**
- Modificar `lib/skill_router.py`
- Modificar `tests/test_skill_router.py`

**Interfaces:**
- Produzir `ExternalCandidate(name: str, source: str, installs: int, url: str)`.
- Produzir `RouterConfig(effort_override: str, external_enabled: bool, threshold: float, timeout_seconds: float, state_dir: Path)`.
- Produzir `extract_search_terms(prompt: str) -> str`.
- Produzir `SkillsCatalog.find(query: str, deadline: float) -> List[ExternalCandidate]`.
- Produzir `SkillsCatalog.use(candidate: ExternalCandidate, deadline: float) -> SkillCandidate`, com `activation_context` contendo a saída completa de uso temporário.
- Produzir `route(prompt: str, client: str, config: RouterConfig, roots: Iterable[Path]) -> RouteDecision`.

- [x] **Passo 1: Criar testes que falham** para redaction, consulta somente em esforço alto, três resultados no máximo, rejeição de identificadores inválidos, ativação temporária, saída `skills use` acima de 512 bytes, cache, CLI ausente, timeout, saída inválida e nenhum termo seguro.
- [x] **Passo 2: Executar os testes e confirmar falha** com `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 3: Implementar o catálogo por subprocesso**. Invocar `skills find <consulta>` e `skills use <origem> --skill <nome>` com argumentos separados, sem shell. Capturar as saídas em arquivos temporários, não em pipes, para preservar respostas longas. Aceitar somente identificadores e links válidos retornados pelo catálogo. Analisar no máximo três candidatos. Compartilhar um prazo total padrão de 15 segundos entre busca e leitura. Comparar os materiais retornados com o mesmo classificador local. Não executar arquivos dos candidatos.
- [x] **Passo 4: Implementar cache com chave SHA-256** dos termos já redigidos e expiração de 24 horas em `$MB_HOME/state/skill-router/`. Não persistir o prompt original.
- [x] **Passo 5: Confirmar falha aberta** quando o CLI não existir, exceder o prazo, retornar saída inválida ou não encontrar termos seguros. Manter a melhor skill local, se existir.
- [x] **Passo 6: Executar os testes e confirmar sucesso** com `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 7: Criar commit local** `feat: add temporary external skill discovery`.

### Tarefa 3: Adaptadores de hooks

**Arquivos:**
- Modificar `lib/skill_router.py`
- Modificar `tests/test_skill_router.py`

**Interfaces:**
- Produzir `handle_hook(client: str, payload: Mapping[str, object], config: RouterConfig) -> Mapping[str, object]`.
- `client` aceita `codex` ou `claude`.
- A entrada lê `prompt` e os campos documentados do cliente. A saída segue o esquema de contexto adicional de `UserPromptSubmit` para aquele cliente.

- [x] **Passo 1: Criar testes que falham** para os formatos de saída de Codex e Claude Code, prompt vazio, JSON malformado e exceção interna.
- [x] **Passo 2: Executar os testes e confirmar falha** com `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 3: Implementar o handler** para ler JSON por `stdin`, chamar `route`, e escrever JSON por `stdout`. O contexto deve indicar skill, origem e razão. Não escrever o prompt ou termos privados em `stderr` ou logs.
- [x] **Passo 4: Confirmar que exceções e falhas de busca produzem saída vazia válida**, sem bloquear o prompt.
- [x] **Passo 5: Executar os testes e confirmar sucesso** com `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 6: Criar commit local** `feat: add prompt hook routing adapters`.

### Tarefa 4: Instalação, remoção e CLI local

**Arquivos:**
- Modificar `lib/skills.py`
- Modificar `lib/skill_router.py`
- Modificar `install.sh`
- Modificar `tests/test_skills.py`
- Modificar `tests/test_hermes.py`
- Modificar `tests/test_skill_router.py`

**Interfaces:**
- `megabrain skill-router status` mostra configuração, fonte de esforço e disponibilidade do catálogo.
- `megabrain skill-router config --effort <auto|low|minimal|medium|high|xhigh|max|ultra> --external <on|off> --threshold <0..1> --timeout <segundos>` grava `$MB_HOME/state/skill-router.json`. O limite padrão é `0.5`; o timeout padrão é `15` segundos.
- `megabrain skill-router setup-catalog` instala `skills` localmente em `$MB_HOME/state/skills-cli/` com `npm --prefix`; só executa após chamada explícita.
- `Installer.install_auto()` registra hooks do Codex e Claude Code e mantém Hermes sem hook dinâmico.

- [x] **Passo 1: Criar testes que falham** para hook Codex e Claude instalado, instalação repetida sem duplicação, preservação de configurações não relacionadas, remoção apenas de entradas Megabrain, configuração CLI e ausência de hook Hermes.
- [x] **Passo 2: Executar os testes e confirmar falha** com `python3 -m unittest discover -s tests -p 'test_skills.py'` e `python3 -m unittest discover -s tests -p 'test_hermes.py'`.
- [x] **Passo 3: Integrar hooks ao ledger existente**. Usar `Installer.edit`, `owned`, `refresh_block` e `uninstall` para registrar e remover somente as alterações do Megabrain. Respeitar caminhos `CODEX_HOME` e os hooks já existentes.
- [x] **Passo 4: Atualizar `ensure_skills_lib` e `install_cli`** para copiar ou obter `skill_router.py` junto de `skills.py`. A instalação remota não pode apontar o hook para um arquivo temporário.
- [x] **Passo 5: Adicionar o comando `megabrain skill-router`** ao dispatch de `install.sh`. Gravar configuração em JSON atômico. O comando `setup-catalog` deve exigir Node/npm e instalar uma versão testada e fixada do pacote `skills` somente dentro do estado do Megabrain.
- [x] **Passo 6: Executar os testes e confirmar sucesso** com `python3 -m unittest discover -s tests -p 'test_skills.py'`, `python3 -m unittest discover -s tests -p 'test_hermes.py'` e `python3 -m unittest discover -s tests -p 'test_skill_router.py'`.
- [x] **Passo 7: Criar commit local** `feat: install effort-aware skill router`.

### Tarefa 5: Documentação e verificação local

**Arquivos:**
- Modificar `README.md`
- Atualizar `docs/superpowers/specs/2026-10-26-contextual-skill-router-design.md` se a implementação exigir decisão nova

- [x] **Passo 1: Documentar as políticas** rápida e de qualidade, a detecção aproximada de esforço, os comandos de configuração, a instalação opcional do catálogo, a expiração do cache e os dados enviados na consulta remota.
- [x] **Passo 2: Executar a suíte completa** com `python3 -m unittest discover -s tests`.
- [x] **Passo 3: Fazer verificação local de instalação e remoção** para Codex e Claude Code com diretórios temporários. Confirmar que Hermes mantém a configuração atual e que arquivos preexistentes continuam iguais.
- [x] **Passo 4: Executar `graphify update .`** para atualizar o grafo de código.
- [x] **Passo 5: Revisar `git diff`** para confirmar que a alteração contém apenas o roteador, a instalação local, testes, documentação e o grafo atualizado.
- [x] **Passo 6: Criar commit local** `docs: document contextual skill router`.

## Revisão final do plano

- O roteamento local, a busca externa por esforço, os hooks, a configuração, a instalação opcional, a falha aberta e a privacidade têm tarefas atribuídas.
- Os testes usam CLI falso ou diretórios temporários. Eles não dependem de rede.
- Skills externas nunca são instaladas permanentemente nem executadas automaticamente.
- O usuário autorizou o push para `main` depois de implementar, revisar e verificar o trabalho local.
