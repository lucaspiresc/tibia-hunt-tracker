# Tibia Hunt Tracker

Aplicativo de desktop para acompanhar itens e spells temporários durante hunts no Tibia. Ele funciona de forma independente do cliente: não lê memória, não envia comandos e não automatiza ações no jogo.

## Funcionalidades do MVP

- Catálogo offline de rings, amulets e spells temporizadas.
- Busca e seleção dos timers usados em cada hunt.
- Pré-alerta configurável e alerta quando o tempo termina.
- Áudios falados com o nome do item ou spell no pré-alerta e no vencimento.
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
