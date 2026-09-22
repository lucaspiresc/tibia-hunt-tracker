# Tibia Hunt Tracker

Aplicativo de desktop para acompanhar itens e spells temporários durante hunts no Tibia. Ele funciona de forma independente do cliente: não lê memória, não envia comandos e não automatiza ações no jogo.

## Funcionalidades do MVP

- Timers manuais exclusivamente para spells; anel e colar usam leitura visual.
- Busca e seleção das spells usadas em cada hunt.
- Pré-alerta configurável e alerta quando o tempo termina.
- Áudios das spells no pré-alerta e no vencimento; “Reequipar anel/colar” quando o slot esvazia.
- Pronúncia editável por timer para nomes e palavras do Tibia.
- Reinício automático a cada ciclo.
- Reinício manual pelo botão `↻` ou duplo clique.
- Presets salvos para diferentes hunts.
- Timer total da hunt.
- Modo compacto e opção de manter a janela sempre visível.

## Executar pelo código

Requer Python 3.11 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

O app gera e guarda os áudios personalizados no primeiro uso. No Windows, os áudios padrão já são incorporados ao executável durante o build para tocar sem atraso.

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

- No pré-alerta, o app fala algo como `Utura. Em 10 segundos.`
- Quando o timer vence, o app fala `Utura.` e reinicia o ciclo.
- O campo **Texto falado** permite ajustar a pronúncia sem mudar o nome exibido.
- Os alertas do Windows não são usados; a reprodução é feita diretamente pelo app.

## Dados

O app lê `data/tracker_catalog.json`. A base foi derivada de dados estruturados do TibiaWiki e validada antes de ser incorporada ao projeto. Consulte `data/README.md` para escopo e atribuição.

## Anel e colar por imagem (0.4, experimental)

1. Abra **Leitura visual** e selecione o monitor do jogo.
2. Deixe o inventário visível, sem outra janela sobre ele. Os itens podem estar equipados.
3. Clique em **Testar áudio**, depois **Iniciar leitura**. Não há marcação de slots.
4. Uma passagem de ocupado para vazio, confirmada em três capturas consecutivas,
   fala **Reequipar anel** ou **Reequipar colar** uma única vez. Equipar novamente
   rearma o aviso. Não há contagem estimada da duração dos itens.

O monitoramento funciona independentemente do botão Iniciar hunt. Timers manuais
e presets aceitam apenas spells. Ao carregar presets antigos, os itens são ignorados;
ao salvar, o arquivo passa ao formato 3, mantendo as configurações das spells.
Retirar manualmente um item também dispara o aviso. A fala identifica o slot,
não o nome do item. Não é necessário gerar os áudios manualmente.

O app inclui uma referência do inventário cinza do manual oficial da CipSoft
(`data/inventory-reference.jpg`; origem em `data/VISUAL_REFERENCE.md`). A localização
usa os controles e as bordas do painel, ignorando os interiores dos dez slots.
Por isso não precisa conhecer cada item nem começar com anel/colar vazios.
Não usa coordenadas fixas da tela, não pede calibração e não grava capturas.
Arquivos `equipment.npz` de versões anteriores não são usados.
Não há consulta de processos,
enumeração de janelas, leitura de memória, comandos ao jogo ou interceptação de teclas.

A busca pode reencontrar o inventário em outra posição. Testa escalas de 75%,
100%, 125%, 150%, 175% e 200% da referência. Outras escalas e aparências, como
o painel dourado da Adventurer's Blessing, não estão validadas.
Correspondências ambíguas e perdas de referência suspendem os
avisos até confirmar novamente um item equipado. Isso pode perder um vencimento
ocorrido enquanto não havia leitura. Um item visualmente muito parecido com o
slot vazio também pode não ser reconhecido. Uma sobreposição restrita ao interior
do slot pode parecer um item: reconhecimento por pixels não distingue todas as oclusões.

O alvo é 5 capturas/s quando os slots estão localizados. Buscas globais são mais
caras e têm intervalo de pelo menos cinco segundos. O painel mostra o
tempo de processamento; não há garantia de desempenho em qualquer resolução.
Parar ou fechar o painel interrompe a leitura. Mantenha o tracker fora da área
do inventário. Nenhum bloqueio de captura é contornado.

Testes automatizados usam a referência oficial com itens sintéticos para transições, escalas, deslocamentos,
ambiguidade e oclusão. Precisão no cliente real e reprodução de áudio no Windows
ainda precisam de validação em jogo; os testes não comprovam compatibilidade universal.

## Regras do Tibia

Não há garantia de ausência de banimento, nem aprovação da CipSoft para este app.
A regra 3b proíbe manipular o cliente ou usar software adicional para jogar;
o comentário oficial cita execução automática de ações (bots/macros).
Isso não constitui uma autorização explícita para leitura de tela com alertas.
Antes de distribuir ou usar a leitura ao vivo no servidor oficial, solicite
confirmação escrita à CipSoft descrevendo exatamente captura passiva, análise
local e alertas, sem comandos ao jogo. Não foi enviada nenhuma consulta em nome
do usuário. A implementação permanece experimental e desligada por padrão.

Fontes oficiais consultadas em 2026-09-22:
- https://www.tibia.com/support/?rule=3b&subtopic=tibiarules
- https://www.tibia.com/support/?page=rules&subtopic=legaldocuments

Referências técnicas:
- https://python-mss.readthedocs.io/stable/examples.html
- https://docs.opencv.org/4.x/da/d0c/tutorial_bounding_rects_circles.html
