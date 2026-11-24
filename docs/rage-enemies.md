# RAGE

Um projétil disparado por um inimigo vermelho transforma o primeiro inimigo
verde básico que atingir em RAGE. O projétil é consumido e não causa dano ao
verde. Paredes, barris e o jogador continuam a bloquear o tiro se estiverem antes
do alvo. Tiros de bosses não aplicam RAGE.

O efeito é permanente, só se aplica uma vez e acumula com Elite e Prismatic:

| Atributo | Alteração sobre o valor atual |
| --- | --- |
| Vida máxima e vida atual | ×2, mantendo a percentagem de vida |
| Dano | ×2, mantendo o limite de 49% da vida máxima do jogador |
| Windup e recovery | ×0,5 |
| Velocidade | ×1,30, até à velocidade base do jogador: 220 |
| XP e moedas | ×2, incluindo os multiplicadores já existentes |

O tamanho de colisão mantém-se. O sprite passa a ter chamas e aparece uma tag
vermelha **RAGE**, adicional à tag Elite/Prismatic. Os sprites incluem movimento,
ataque, recuperação e morte; os recortes estão no catálogo partilhado.

Os projéteis vermelhos atravessam vermelhos, bosses e inimigos já RAGE. Um
vermelho Elite/Prismatic continua a ser vermelho e não pode receber o efeito.
Um verde Elite/Prismatic pode recebê-lo e conserva as suas recompensas especiais.

Arte e resumos dos prompts: [assets/rage/README.md](../assets/rage/README.md).
