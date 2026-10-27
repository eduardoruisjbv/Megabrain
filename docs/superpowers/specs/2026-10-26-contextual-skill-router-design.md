# Roteador de skills por contexto

## Intenção

O Megabrain deve ativar a skill mais útil para cada solicitação. O roteador deve usar skills instaladas com baixa latência. Em esforço alto, deve consultar um catálogo externo quando o catálogo local não tiver uma correspondência confiável.

## Estado atual

`Installer.install_auto` já habilita a seleção implícita de skills instaladas para Codex, Claude Code e Hermes. Ele atualiza blocos de instruções e metadados das skills. Ele não classifica cada prompt, não aplica política por esforço e não pesquisa novas skills durante uma solicitação.

`Installer.skill_roots` localiza skills pessoais e plugins ativos. `install_collection` instala coleções de repositórios fixados. O roteador deve aproveitar essas funções e preservar o controle de arquivos que o instalador já mantém.

## Objetivos

- Escolher uma ou mais skills instaladas conforme o contexto do prompt.
- Usar apenas dados locais quando o esforço for baixo, médio ou desconhecido.
- Em esforço alto, pesquisar fora apenas quando a correspondência local ficar abaixo de um limite configurado.
- Expor a skill escolhida, a origem e uma razão curta para a decisão.
- Manter a busca externa desligável e evitar instalar skills externas sem confirmação.
- Integrar Codex, Claude Code e Hermes sem substituir a seleção nativa de skills.

## Fora do escopo

- Interceptar ou redirecionar chamadas ao modelo por um proxy LiteLLM.
- Fazer chamadas adicionais a um modelo para classificar cada prompt.
- Executar scripts de skills externas durante a descoberta.
- Instalar automaticamente skills externas de forma permanente.
- Criar um mecanismo geral de pesquisa para MCPs ou plugins.

## Requisitos

### Política por esforço

O roteador agrupa `low`, `minimal`, `medium` e valores desconhecidos na política rápida. Essa política consulta somente o índice local. `high`, `xhigh`, `max` e `ultra` ativam a política de qualidade. Essa política pesquisa skills externas somente quando nenhuma skill local alcança o limite de correspondência.

O valor `auto` usa a política rápida. Uma substituição explícita do Megabrain tem prioridade. Em seguida, o adaptador lê o sinal do hook quando existe, depois valores documentados do ambiente ou da configuração local do cliente. Codex e Claude Code não expõem o valor efetivo de cada solicitação de forma uniforme. Portanto, essa leitura é aproximada. Se o roteador não encontrar um valor conhecido, ele usa a política rápida.

Codex e Claude Code oferecem hooks no envio do prompt que podem adicionar contexto ao modelo. O adaptador deve ler apenas sinais documentados e suportar uma configuração explícita do Megabrain como substituição. A detecção aproximada é aceita. O comando `megabrain skill-router status` deve exibir a política atual. O comando `megabrain skill-router config` deve permitir ajuste do esforço padrão.

### Correspondência local

Um serviço `SkillRouter` deve indexar nome, descrição, caminho e origem das skills descobertas por `Installer.skill_roots`. O instalador deve registrar as raízes de skills ativas de cada cliente. O roteador deve guardar nome e descrição em um índice local com validade curta. Ele deve invalidar esse índice quando o Megabrain instalar ou remover skills. A seleção deve usar correspondência determinística sobre metadados, sem chamada a um modelo.

O roteador ativa apenas skills com pontuação acima do limite. Se nenhuma alcançar o limite, ele não injeta uma skill local. A seleção nativa do cliente continua disponível.

### Descoberta externa

Na política de qualidade, o roteador consulta o CLI oficial `skills` do catálogo Skills, com `skills find` para a descoberta e `skills use` para obter uma skill de uso temporário. O roteador não deve instalar a skill nos diretórios permanentes dos clientes. O CLI oferece busca por consulta e `skills use` resolve a origem para uma área temporária. O Megabrain deve detectar a ausência do CLI e oferecer a configuração explícita. Não deve instalar ou executar esse CLI em silêncio.

O roteador deve analisar no máximo os três primeiros resultados externos. Ele deve obter o `SKILL.md` de cada resultado por meio de `skills use`, aplicar o mesmo classificador local aos metadados obtidos e ativar o candidato com a maior pontuação acima do limite. Essa análise não executa scripts. Se a busca retornar mais candidatos do que o tempo permitido, ela interrompe a busca e usa o melhor resultado já analisado.

A consulta deve conter apenas termos de tópico extraídos deterministicamente do prompt. O roteador deve remover caminhos locais, endereços de e-mail e padrões de segredo antes de enviar a consulta. Se não restarem termos úteis, o roteador deve ignorar a busca externa.

O roteador deve comparar os resultados externos com as skills locais. Quando uma skill externa tiver correspondência clara, o roteador pode carregá-la para uso temporário nessa solicitação e informar sua origem. O roteador não deve instalá-la de forma permanente sem confirmação. O roteador não deve executar scripts externos. Se a confiança for baixa ou a busca falhar, ele mantém o resultado local e informa que não encontrou uma skill melhor.

O cache local guarda consultas externas por 24 horas e metadados de skills por 60 segundos. O instalador registra as raízes ativas de cada cliente e invalida o índice local quando o Megabrain instala ou remove skills. O limite remoto padrão é 15 segundos e o comando de configuração aceita até 60 segundos. O hook de cliente usa um timeout de 65 segundos. A busca pode ser desativada. Erros de rede nunca bloqueiam o prompt.

### Adaptadores de cliente

- **Codex:** usar `UserPromptSubmit` para receber o prompt e devolver contexto adicional. A configuração de hook deve respeitar a revisão e confiança exigidas pelo Codex.
- **Claude Code:** usar `UserPromptSubmit` para receber o prompt e adicionar contexto. Preservar os hooks e configurações existentes.
- **Hermes:** manter as instruções atuais de seleção implícita. Só ativar busca dinâmica se o cliente expuser um ponto de integração com suporte documentado. Caso contrário, manter a descoberta nativa sem esforço condicionado.

Cada adaptador deve falhar aberto para o cliente: erro, timeout ou resposta inválida do roteador não deve bloquear a solicitação do usuário.

## Transparência e privacidade

O Megabrain deve indicar se escolheu uma skill local, uma skill externa temporária ou nenhuma skill. Para uma skill externa, deve mostrar nome, mantenedor e link de origem. A consulta remota deve enviar somente termos de tópico redigidos, nunca o prompt completo nem conteúdo do repositório.

O conteúdo externo deve ser tratado como instrução de terceiros. A ativação temporária marca a saída como contexto externo não confiável. Ela não concede autoridade para ignorar as instruções do usuário, de sistema ou do cliente.

## Interface

Adicionar `megabrain skill-router status`, `config` e `setup-catalog`. Os comandos permitem ver a política, ajustar esforço, busca externa, limite e timeout, e instalar o catálogo opcional. O roteamento local fica ativo quando `skills-auto` está ativo. A busca externa só ocorre em esforço alto. Skills externas nunca são instaladas permanentemente sem uma ação explícita.

## Abordagens consideradas

1. **Skill-meta:** simples e portátil, mas depende da decisão do modelo e não impõe uma política confiável de latência.
2. **Roteador local com adaptadores por cliente:** escolhido pelo usuário. Usa hooks para classificar solicitações no host, consulta skills locais primeiro e pesquisa externamente apenas em esforço alto. Mantém falha aberta e a instalação separada da descoberta.
3. **Proxy da API do modelo:** centraliza o roteamento, mas exige que cada cliente use um endpoint intermediário e adiciona complexidade de autenticação e compatibilidade.

## Chamadas para o implementador

- Escolher o formato de cache e o algoritmo local mais simples que atenda à latência.
- Isolar o CLI `skills` atrás de uma interface substituível para permitir outros catálogos no futuro.
- Usar os mecanismos de configuração e de propriedade de arquivos já existentes no Megabrain.
- Criar verificações unitárias para as regras de esforço, limites, falha aberta, limpeza de dados sensíveis e preservação de configurações do cliente.

## Referências

- Codex Skills: https://developers.openai.com/plugins/concepts/skills
- Codex Hooks: https://developers.openai.com/codex/hooks
- Claude Code Hooks: https://code.claude.com/docs/en/hooks
- Skills CLI e descoberta: https://www.skills.sh/docs/cli
