# DOWNGRADE — Roteiro do Jogo

> Ação 2D de um golpe só. Neon, sujeira, câmera lenta.
> 9 fases · 3 atos · 1 chip que não deveria existir.

---

## 1. Premissa

Em **Nova Ferrugem**, todo mundo tem uma **Escama**: um chip de comando implantado na nuca que dá ao portador uma habilidade (força, mira, reflexo, armas integradas). Quem fabrica as Escamas é a **Ofídia**, uma corporação que lança uma geração nova a cada ano e larga as antigas no lixo, junto com os donos.

**Marco** é catador no **Aterro 9**, o maior lixão da cidade. Ele não tem Escama porque nunca pôde pagar por uma. Uma noite, revirando sucata, ele encontra um **cadáver** com uma Escama ainda acesa na nuca.

O chip parece velho, quebrado, **nível 0**. Mas é a **Escama de última geração** da Ofídia: o protótipo **MUDA**, a única Escama capaz de **absorver o poder de outras Escamas**. A dona anterior roubou o chip e fez um **downgrade** de fábrica nele, apagando tudo até o nível zero pra que a Ofídia não conseguisse rastreá-lo.

Quando Marco implanta o chip, o rastreio volta a funcionar. **A Ofídia quer a Escama de volta**, e quer Marco morto.

### Tema
*Downgrade* é o que a cidade faz com as pessoas: troca, descarta, rebaixa. No final, também é a arma de Marco contra a Ofídia.

---

## 2. Personagens

| Personagem | Papel | Descrição |
|---|---|---|
| **Marco** | Protagonista | Catador do Aterro 9, ~20 anos. Calado, prático, sem nada a perder. Não queria ser herói, só queria vender o chip. |
| **ECO** | Guia / voz na cabeça | Resíduo de memória da antiga dona, gravado na Escama. Fala com Marco em fragmentos. Começa fria e técnica e fica mais humana conforme o chip upa. |
| **Helena Duarte** | O cadáver | Engenheira-chefe do Projeto MUDA. Roubou o protótipo ao descobrir para que a Ofídia ia usá-lo. Morreu no lixão, baleada. A identidade dela é revelada aos poucos. |
| **Rato** | Chefe do Ato 1 | Rei do Aterro 9. Controla os catadores e tem uma Escama de canhão no braço. A Ofídia pagou a ele para achar o chip. |
| **Agente Vidro** | Chefe do Ato 2 | Caçadora de elite da Ofídia. A Escama dela desacelera a percepção do tempo. Fria, educada, letal. |
| **Diretor Caetano Rios** | Antagonista final | Diretor do Projeto MUDA. Quer usar a Escama de última geração pra controlar todas as Escamas da cidade a partir de um único chip. |

---

## 3. A Escama de Marco — Árvore de Habilidades

Marco ganha **fragmentos** ao absorver a Escama de inimigos de elite e ao achar colecionáveis escondidos (chips perdidos). Cada fragmento sobe **1 nível** de uma habilidade já desbloqueada.

### Espada (desde a fase 1)
| Nível | Efeito |
|---|---|
| 0 | Corte curto e lento. Um golpe mata inimigos comuns. |
| 1 | Alcance maior. |
| 2 | **Rebate projéteis** de volta no atirador. |
| 3 | **Corte-investida**: um dash curto que atravessa inimigos. |
| 4 | Combo aéreo: corte para baixo durante o pulo. |
| 5 | Corta **escudos** e portas blindadas. |

### Canhão (absorvido do Rato, fim da fase 3)
| Nível | Efeito |
|---|---|
| 0 | Tiro reto, recarga lenta. |
| 1 | Recarga mais rápida. |
| 2 | **Tiro perfurante**: atravessa vários inimigos. |
| 3 | Tiro carregado que destrói paredes frágeis e abre atalhos. |
| 4 | Ricochete em superfícies metálicas. |

### Overtime (absorvido da Agente Vidro, fim da fase 6)
Marco vê tudo em câmera lenta, mas **o chip usa o corpo dele como bateria**: a vida drena enquanto o Overtime está ativo. Se a vida zerar, Marco morre.

| Nível | Efeito |
|---|---|
| 0 | Câmera lenta forte, dreno alto. |
| 1 | Dreno menor. |
| 2 | Matar um inimigo durante o Overtime **devolve um pouco de vida**. |
| 3 | Dreno ainda menor. |
| 4 | **Overtime perfeito**: rebater uma bala no Overtime não drena vida por 1 segundo. |

> Regra de design: a árvore nunca tem mais que 2 escolhas boas ao mesmo tempo. O jogador sempre sabe o que quer upar em seguida.

---

## 4. Estrutura — 3 Atos, 9 Fases

| Ato | Fases | Local | Habilidade nova | Chefe |
|---|---|---|---|---|
| I — Sucata | 1, 2, 3 | Aterro 9 | Espada (nv 0) | Rato → **Canhão** |
| II — Cidade | 4, 5, 6 | Nova Ferrugem | Canhão | Agente Vidro → **Overtime** |
| III — Ofídia | 7, 8, 9 | Torre Ofídia | Overtime | Diretor Rios |

Cada fase introduz **uma** ideia nova (inimigo, armadilha ou mecânica), testa essa ideia sozinha e depois a combina com o que o jogador já conhece.

---

## 5. Roteiro das Fases

### ATO I — SUCATA

#### Fase 1 — O Lixão
- **História:** Chuva ácida sobre o Aterro 9. Marco acha o cadáver no meio de um monte de eletrônicos. Ele arranca a Escama pra vender, mas ela se **implanta sozinha** na nuca dele. ECO acorda: *"Portador detectado. Nível zero. ...Você não é ela."* Catadores do Rato viram o brilho do chip e vêm atrás.
- **Ensina:** andar, pular, Espada nv 0, morrer com 1 golpe, reiniciar rápido.
- **Inimigos:** Catador (corpo a corpo, lento).
- **Level design:** horizontal, montes de sucata como plataformas, sem armadilhas. Ninguém atira.
- **Fim:** ECO marca no mapa um sinal de rastreio. *"Eles sabem onde estamos."*

#### Fase 2 — O Desmanche
- **História:** Marco foge pelo desmanche de carros do Rato e descobre que a Ofídia pôs preço na cabeça dele. ECO revela o primeiro fragmento de memória: um laboratório, um nome, "Helena".
- **Ensina:** inimigos que atiram (precisa pular as balas ou se aproximar por cima) e **portas** que só abrem matando todos da sala.
- **Inimigos:** Catador, **Pistoleiro**.
- **Level design:** salas fechadas em sequência, prensas hidráulicas que esmagam em ritmo e são uma ameaça de timing.
- **Colecionável:** primeiro chip perdido (+1 fragmento). O jogador sobe a **Espada para nv 1**.

#### Fase 3 — A Torre de Prensa  *(CHEFE: Rato)*
- **História:** O Rato fecha o lixão e espera Marco no topo da torre de prensa. *"Esse chip vale mais que o lixão inteiro, garoto."*
- **Ensina:** subida vertical e combate em arena.
- **Inimigos:** Catador, Pistoleiro, **Cão-Sucata** (rápido, pula em você).
- **Chefe — Rato:** o braço-canhão dispara uma rajada telegrafada (o braço brilha antes). Marco tem que se aproximar entre as rajadas. Na fase 2 da luta, a plataforma desaba em partes.
- **Fim:** Marco vence, e a Escama **absorve** a do Rato. Primeira absorção: Marco sente o chip "comer" o outro, e ECO fala pela primeira vez com emoção: *"Isso... foi pra isso que ela me fez."* **Desbloqueia o CANHÃO.**

### ATO II — CIDADE

#### Fase 4 — Mercado Noturno
- **História:** Marco entra na cidade atrás de um mecânico de Escamas pirata que talvez saiba tirar o chip. O mercado está cheio de agentes da Ofídia disfarçados.
- **Ensina:** o Canhão contra **inimigos distantes** e **civis** no cenário (matar civis zera o rank da fase).
- **Inimigos:** Pistoleiro, **Atirador de elite** (laser de mira visível), **Escudeiro** (escudo frontal: atacar por trás, por cima ou com o Canhão).
- **Level design:** neon, telhados e vielas, várias rotas.
- **Fim:** o mecânico diz que o chip **não sai**: está fundido ao sistema nervoso de Marco. E conta que a Escama é a de **última geração**.

#### Fase 5 — Metrô Suspenso
- **História:** Fuga pelo trem elevado, com a Agente Vidro perseguindo. Ela aparece, mata tudo em câmera lenta na frente de Marco e some. *"Devolva o que é nosso. É a única oferta."*
- **Ensina:** **cenário em movimento**: vagões, túneis que obrigam a abaixar, saltos entre trens.
- **Inimigos:** Agentes Ofídia (dash curto), **Drones**.
- **Level design:** autoscroll em partes, com pausas em vagões-arena.
- **Fragmento de memória:** Helena descobriu que o MUDA não foi feito pra absorver poderes, e sim pra **controlar** outras Escamas.

#### Fase 6 — Clínica Ofídia  *(CHEFE: Agente Vidro)*
- **História:** Marco invade uma clínica onde a Ofídia faz "upgrades obrigatórios" em quem tem Escama antiga, e descobre pacientes sem consciência, com o chip controlado remotamente.
- **Ensina:** **lasers** que ligam e desligam, câmeras de segurança que chamam reforço.
- **Chefe — Agente Vidro:** ela usa o Overtime de verdade e fica rápida demais pra acompanhar. Marco precisa usar o cenário: destruir as luzes com o Canhão (ela perde a vantagem no escuro) e rebater as balas dela com a Espada nv 2.
- **Fim:** Marco absorve a Escama dela. **Desbloqueia o OVERTIME.** Ele usa pela primeira vez, e o nariz sangra. ECO: *"Ela também sangrava. Por isso escondeu o chip. Ele come quem usa."*

### ATO III — OFÍDIA

#### Fase 7 — A Fábrica de Escamas
- **História:** Marco entra na Torre Ofídia pela fábrica. Linhas de montagem produzindo milhares de Escamas novas, todas com uma "porta dos fundos" ligada ao MUDA.
- **Ensina:** **Overtime em situações reais**: esteiras rápidas, braços robóticos, salas que exigem câmera lenta pra passar sem gastar vida demais.
- **Inimigos:** Torretas, Escudeiros de elite, Agentes Ofídia.
- **Level design:** quebra-cabeça de timing, sempre com uma rota mais lenta e segura e uma rápida e arriscada.

#### Fase 8 — O Servidor
- **História:** Marco chega ao núcleo de dados. ECO revela tudo: Helena fez o downgrade do chip pra zero e fugiu, mas foi seguida e morta no lixão. O Diretor Rios vai lançar a **"Atualização Final"**, que coloca todas as Escamas da cidade sob controle do MUDA.
- **Ensina:** **combinar tudo**: Espada, Canhão e Overtime numa mesma sala.
- **Inimigos:** todos os anteriores, em ondas.
- **Level design:** fase mais longa, sem checkpoints no meio das salas-arena. É a prova final antes do chefe.
- **Escolha de build:** últimos fragmentos do jogo; o jogador fecha a árvore como preferir.

#### Fase 9 — O Topo da Torre  *(CHEFE FINAL: Diretor Rios)*
- **História:** Rios implantou uma **cópia do MUDA** em si mesmo. Ele tem Espada, Canhão e Overtime, sem o mesmo custo, porque drena a vida dos funcionários conectados à rede.
- **Chefe — 3 fases:**
  1. **Espelho:** Rios usa os mesmos golpes que Marco.
  2. **Rede:** Rios puxa Escamas de funcionários e invoca reforços. Marco precisa cortar os cabos de conexão com o Canhão.
  3. **Overtime contra Overtime:** os dois em câmera lenta. A vida de Marco drena e a única chance é rebater a bala final.
- **Final:** Rios cai. A Atualização Final já está em 99%. ECO explica que só existe um jeito de parar: Marco usar o MUDA pra forçar um **DOWNGRADE** em todas as Escamas da cidade, voltando todas, inclusive a dele, ao **nível zero**.
- Marco aperta o comando. A cidade apaga. Ninguém controla ninguém. A Escama de Marco volta pra **nível 0, só a Espada**, e ECO se despede com a voz de Helena: *"Obrigada por terminar o que eu não consegui."*
- **Pós-créditos:** Marco no Aterro 9 de novo. Um chip pisca no meio da sucata.

---

## 6. Inimigos

| Inimigo | Aparece na fase | Comportamento | Como vencer |
|---|---|---|---|
| Catador | 1 | Anda e ataca de perto | Espada |
| Pistoleiro | 2 | Atira em linha reta com aviso | Pular a bala ou rebatê-la (Espada nv 2) |
| Cão-Sucata | 3 | Corre e pula | Timing ou Overtime |
| Atirador de elite | 4 | Laser de mira e tiro instantâneo | Sair da linha ou Canhão |
| Escudeiro | 4 | Escudo frontal | Atacar por trás ou de cima, ou Espada nv 5 |
| Agente Ofídia | 5 | Dash e tiro | Esperar o dash e contra-atacar |
| Drone | 5 | Voa e persegue | Canhão |
| Torreta | 7 | Fixa, rajada giratória | Overtime para atravessar |

---

## 7. Regras de Level Design

1. **Um golpe mata**, tanto Marco quanto os inimigos comuns. Reiniciar a sala é instantâneo.
2. **Cada sala é um quebra-cabeça** de ordem: em que inimigo ir primeiro?
3. **Toda ameaça é telegrafada**: brilho, som ou laser antes do ataque.
4. **O Overtime é um recurso, não um botão de vitória**: as salas do Ato III têm uma solução sem ele, mais difícil.
5. **Ranking por fase** (tempo + mortes) salvo no backend Java, em `/api/scores/{fase}`.
6. Mapas feitos no **Tiled** com as camadas:
   - `solidos` (tiles): chão e paredes
   - `spawns` (objetos): tipo `marco` (exatamente 1), `inimigo`, `chefe`
   - validados por `POST /tools/levels/validate` antes de entrar no jogo

---

## 8. Mapa do Projeto ↔ Jogo

| Pasta | Função no jogo |
|---|---|
| `downgrade-game/` | O jogo (Angular + Phaser) |
| `downgrade-game/src/app/game/escama/` | A Escama de Marco e a árvore de habilidades |
| `downgrade-game/src/app/game/scenes/` | Uma cena por fase (`lixao.scene.ts` = fase 1) |
| `downgrade-game/public/assets/fases/` | Mapas do Tiled (`fase-1-lixao.json` … `fase-9-topo-da-torre.json`) |
| `downgrade-api/` | Backend Java: ranking, progresso, saves |
| `downgrade-tools/` | Python: validação de fases |
| `nginx/` | Porta de entrada: junta tudo em `localhost` |
| `docs/` | Este roteiro |
