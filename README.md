# Tibia Hunt Tracker

Aplicativo de desktop para acompanhar itens e spells temporários durante hunts no Tibia. Ele funciona de forma independente do cliente: não lê memória, não envia comandos e não automatiza ações no jogo.

## Funcionalidades do MVP

- Catálogo offline de rings, amulets e spells temporizadas.
- Busca e seleção dos timers usados em cada hunt.
- Pré-alerta configurável e alerta quando o tempo termina.
- Notificação do Windows, som e voz usando os recursos locais do computador.
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

As dependências de voz e notificação são opcionais. Se não estiverem disponíveis, o app continua funcionando e usa um alerta sonoro simples.

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

O executável será criado em `dist\TibiaHuntTracker.exe`.

### Build automático no GitHub

Cada push na branch `main` executa os testes e gera um artefato chamado `TibiaHuntTracker-Windows` na aba **Actions** do repositório. Baixe o artefato e extraia o `.exe` para executar o app.

## Dados

O app lê `data/tracker_catalog.json`. A base foi derivada de dados estruturados do TibiaWiki e validada antes de ser incorporada ao projeto. Consulte `data/README.md` para escopo e atribuição.
