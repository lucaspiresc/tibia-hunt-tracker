# Tibia Hunt Tracker

Aplicativo de desktop com timers manuais para itens e spells temporários durante hunts no Tibia. Anéis, colares e spells usam o mesmo fluxo: escolha no catálogo, configure o tempo e inicie a hunt. O app não captura a tela, não lê memória do jogo e não envia comandos ao cliente.

## Funcionalidades

- Catálogo pesquisável de itens e spells com duração fixa.
- Duração, pré-alerta e texto falado configuráveis por timer.
- Áudio com o nome do item ou spell no pré-alerta e no vencimento.
- Reinício automático da contagem a cada ciclo.
- Reinício manual pelo botão `↻` ou duplo clique.
- Presets salvos para diferentes hunts.
- Timer total da hunt.
- Modo compacto e opção de manter a janela sempre visível.

## Como usar

1. Busque um item ou spell em **Itens e spells** e clique em **Adicionar →**.
2. Ajuste **Duração**, **Avisar antes (s)** e **Texto falado**. Marque **Áudio falado** e clique em **Aplicar**.
3. Adicione os demais timers e salve o preset.
4. Clique em **INICIAR HUNT** ao começar a usar os itens e spells.
5. Ao reequipar um item ou renovar uma spell em outro momento, use `↻` ou dê duplo clique no timer para sincronizá-lo.

Todos os timers começam juntos ao iniciar a hunt. Ao vencer, cada timer avisa e reinicia a contagem; isso não equipa itens nem lança spells no jogo. Se um efeito terminar antes do tempo, ajuste o timer manualmente. Termine a hunt antes de alterar os timers ou trocar o preset.

Os presets existentes continuam sendo carregados, inclusive configurações de áudio. Itens presentes em presets antigos voltam a aparecer. Itens que já foram removidos ao salvar nas versões com leitura visual precisam ser adicionados novamente. Não é necessário marcar o inventário nem configurar captura de tela.

## Executar pelo código

Requer Python 3.11 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

O app gera e guarda os áudios personalizados no primeiro uso. No Windows, os áudios padrão de itens e spells são incorporados ao executável durante o build. Não é necessário gerar os áudios manualmente para usar o executável.

## Testes

```powershell
pip install -r requirements-dev.txt
pip install -e .
python -m unittest discover -s tests -v
```

## Gerar o executável do Windows

```powershell
.\scripts\build_windows.ps1
```

O script gera os `.wav` do catálogo com a voz do Windows e cria o executável em `dist\TibiaHuntTracker.exe`. Se houver uma voz em português instalada, ela será priorizada.

### Build automático no GitHub

Cada push na branch `main` executa os testes, gera os áudios e publica um artefato chamado `TibiaHuntTracker-Windows` na aba **Actions** do repositório. Baixe o artefato e extraia o `.exe` para executar o app.

## Como funcionam os alertas

- No pré-alerta, o app fala algo como `Sword Ring. Em 30 segundos.` ou `Utura. Em 10 segundos.`
- Quando o timer vence, o app fala o nome configurado e reinicia o ciclo.
- O campo **Texto falado** permite ajustar a pronúncia sem mudar o nome exibido.
- Os alertas do Windows não são usados; a reprodução é feita diretamente pelo app.

## Dados

O app lê `data/tracker_catalog.json`. A base foi derivada de dados estruturados do TibiaWiki. Consulte `data/README.md` para escopo e atribuição.

Este projeto não é afiliado nem aprovado pela CipSoft. Seu funcionamento se limita a contagem de tempo configurada pelo usuário e alertas locais.
