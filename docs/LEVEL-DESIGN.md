# Como criar uma fase no Tiled

## 1. Abrir o projeto
No Tiled: **File > Open File or Project** → `tiled/downgrade.tiled-project`.
Isso mostra a pasta de assets no painel *Project* e registra as classes de objeto
(`marco`, `catador`, `pistoleiro`, `saida`, `chefe`) com cor e propriedades.

## 2. Partir de uma fase existente
O jeito mais fácil: abra `downgrade-game/public/assets/fases/fase-1-lixao.json` e use
**File > Save As** com o nome da nova fase, por exemplo `fase-2-desmanche.json`.
O nome do arquivo precisa começar com `fase-`.

Para criar do zero (**File > New > New Map**):
- Orientation **Orthogonal**, Tile layer format **CSV**, Tile size **32 x 32**
- **Desmarque "Infinite"**
- Altura de **17 tiles** (a tela tem 540px). A largura é livre: 60 tiles = 2 telas.
- Adicione o tileset `downgrade-game/public/assets/tiles/blocos.png` com o nome **blocos**,
  tiles 32x32, e marque **Embed in map**.

## 3. Camadas obrigatórias
| Camada | Tipo | O que vai nela |
|---|---|---|
| `solidos` | Tile Layer | Chão, paredes, plataformas. **Todo tile aqui colide** e bloqueia a visão dos inimigos. |
| `spawns` | Object Layer | Retângulos com a classe certa (campo *Class*). |

## 4. Objetos (camada `spawns`)
Desenhe um **retângulo** e escolha a *Class*. **A base do retângulo é onde os pés ficam.**

| Class | Quantidade | Propriedades |
|---|---|---|
| `marco` | exatamente 1 | — |
| `saida` | exatamente 1 | — (o tamanho do retângulo é o tamanho da porta) |
| `catador` | quantos quiser | `patrulha` (px para cada lado, padrão 80) |
| `pistoleiro` | quantos quiser | — |
| `chefe` | reservado para as fases 3, 6 e 9 | `quem` |

Nas propriedades do mapa (**Map > Map Properties**), adicione `nome` (string) com o nome da fase.

## 5. Colocar no jogo
1. Salve o JSON em `downgrade-game/public/assets/fases/`.
2. Em `downgrade-game/src/app/game/fases/fases.ts`, preencha o `mapa` da fase.
3. Valide sem subir tudo:
   ```
   cd downgrade-tools
   python -m app.validar ../downgrade-game/public/assets/fases
   ```
4. `docker compose up -d --build`. **Se alguma fase tiver erro, o build falha** e mostra o que corrigir.

## Dicas de design (do roteiro)
- Toda ameaça precisa ser vista antes de matar: coloque Pistoleiros onde o jogador consiga ver o laser.
- Use blocos em `solidos` para quebrar a linha de visão e criar rotas de aproximação.
- Cada fase introduz **uma** ideia nova; teste-a sozinha antes de combinar.
